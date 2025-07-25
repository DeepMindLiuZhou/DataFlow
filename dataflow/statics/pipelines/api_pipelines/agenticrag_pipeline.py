from dataflow.operators.generate import (
    AutoPromptGenerator,
    QAGenerator,
    QAScorer
)

from dataflow.operators.filter import (
    ContentChooser
)

from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.serving import LocalModelLLMServing_vllm

class AgenticRAG_APIPipeline():
    def __init__(self):

        self.storage = FileStorage(
            first_entry_file_name="../example_data/AgenticRAGPipeline/pipeline_small_chunk.json",
            cache_path="./cache_local",
            file_name_prefix="dataflow_cache_step",
            cache_type="json",
        )

        # use API server as LLM serving
        self.llm_serving = APILLMServing_request(
                api_url="https://api.openai.com/v1/chat/completions",
                model_name="gpt-4o",
                max_workers=1
        )

        embedding_serving = APILLMServing_request(
                    api_url="https://api.openai.com/v1/embeddings",
                    model_name="text-embedding-ada-002",
                    max_workers=100
        )

        self.content_chooser_step1 = ContentChooser(embedding_serving=embedding_serving, num_samples=5, method="random")

        self.prompt_generator_step2 = AutoPromptGenerator(self.llm_serving)

        self.qa_generator_step3 = QAGenerator(self.llm_serving)

        self.qa_scorer_step4 = QAScorer(self.llm_serving)
        
    def forward(self):

        self.content_chooser_step1.run(
            storage = self.storage.step(),
            input_key = "text"
        )

        self.prompt_generator_step2.run(
            storage = self.storage.step(),
            input_key = "text"
        )

        self.qa_generator_step3.run(
            storage = self.storage.step(),
            input_key="text",
            prompt_key="generated_prompt",
            output_quesion_key="generated_question",
            output_answer_key="generated_answer"
        )

        self.qa_scorer_step4.run(
            storage = self.storage.step(),
            input_question_key="generated_question",
            input_answer_key="generated_answer",
            output_question_quality_key="question_quality_grades",
            output_question_quality_feedback_key="question_quality_feedbacks",
            output_answer_alignment_key="answer_alignment_grades",
            output_answer_alignment_feedback_key="answer_alignment_feedbacks",
            output_answer_verifiability_key="answer_verifiability_grades",
        )
        
if __name__ == "__main__":
    model = AgenticRAG_APIPipeline()
    model.forward()
