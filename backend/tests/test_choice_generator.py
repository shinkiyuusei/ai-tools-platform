import importlib.util
from pathlib import Path
import unittest


_MODULE_PATH = Path(__file__).parents[1] / "app" / "services" / "chat" / "choice_generator.py"
_SPEC = importlib.util.spec_from_file_location("choice_generator", _MODULE_PATH)
choice_generator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(choice_generator)


class ChoiceGeneratorTestCase(unittest.TestCase):
    def test_uses_the_latest_narrative_and_preserves_model_generated_choices(self):
        class FakeAdapter:
            def chat_completion(self, *, messages, **_kwargs):
                self.messages = messages
                return {
                    "choices": [{"message": {"content": "A. 追问遗失的信件\nB. 暂时离开书房\nC. 检查窗边的脚印\nD. 将信件投入壁炉"}}],
                    "usage": {"total_tokens": 17},
                }

        adapter = FakeAdapter()
        block, tokens = choice_generator.generate_choice_block(adapter, "test-model", "艾琳把信藏进抽屉。")

        self.assertIn("艾琳把信藏进抽屉。", adapter.messages[1]["content"])
        self.assertEqual(tokens, 17)
        self.assertEqual(
            block,
            "\n\n【抉择分支】\nA. 追问遗失的信件\nB. 暂时离开书房\nC. 检查窗边的脚印\nD. 将信件投入壁炉\n",
        )

    def test_rejects_incomplete_model_output_instead_of_inventing_fixed_choices(self):
        self.assertEqual(choice_generator.format_choice_block("A. 继续当前行动\nB. 换个方式"), "")
