import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.social_farm.renderer import (
    CANVAS_SIZE,
    OBJECT_BACKGROUNDS,
    PERSON_BACKGROUNDS,
    render_slide,
    validate_copy,
)
from app.social_farm.topics import TOPICS


class SocialFarmContentTests(unittest.TestCase):
    def test_local_photo_library_has_enough_unique_backgrounds(self) -> None:
        self.assertGreaterEqual(len(OBJECT_BACKGROUNDS), 6)
        self.assertGreaterEqual(len(PERSON_BACKGROUNDS), 2)
        for path in (*OBJECT_BACKGROUNDS, *PERSON_BACKGROUNDS):
            self.assertTrue(path.exists(), path)

    def test_topic_bank_has_safe_six_slide_stories(self) -> None:
        self.assertGreaterEqual(len(TOPICS), 15)
        self.assertEqual(len({topic.key for topic in TOPICS}), len(TOPICS))

        for topic in TOPICS:
            self.assertEqual(len(topic.slides), 5, topic.key)
            self.assertLessEqual(
                sum(slide.visual_type == "person_far" for slide in topic.slides),
                2,
                topic.key,
            )
            self.assertTrue(
                all(
                    slide.visual_type in {"object", "room", "person_far", "interface"}
                    for slide in topic.slides
                ),
                topic.key,
            )
            self.assertEqual(validate_copy("cover", topic.title, []), [], topic.key)
            self.assertIn("televera.se", topic.cta.lower(), topic.key)
            televera_slides = 0
            for slide in topic.slides:
                self.assertEqual(
                    validate_copy("body", slide.heading, list(slide.body)),
                    [],
                    f"{topic.key}: {slide.heading}",
                )
                slide_text = " ".join((slide.heading, *slide.body)).lower()
                televera_slides += "televera" in slide_text
            self.assertEqual(
                televera_slides,
                1,
                f"{topic.key}: exakt en slide ska nämna Televera",
            )

    def test_topic_bank_avoids_ai_sounding_phrases(self) -> None:
        banned_phrases = (
            "gav mig överblick",
            "fick ett sammanhang",
            "det jag egentligen sparade",
            "helhetsbedömningen",
            "i lugn och ro",
            "utan stress",
        )
        for topic in TOPICS:
            active_copy = " ".join(
                (
                    topic.title,
                    topic.caption,
                    topic.cta,
                    *(
                        text
                        for slide in topic.slides
                        for text in (slide.heading, *slide.body)
                    ),
                )
            ).lower()
            for phrase in banned_phrases:
                self.assertNotIn(phrase, active_copy, f"{topic.key}: {phrase}")

    def test_renderer_produces_tiktok_sized_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cover_path = Path(temp_dir) / "cover.png"
            body_path = Path(temp_dir) / "body.png"

            render_slide(
                output_path=cover_path,
                position=0,
                kind="cover",
                heading="5 saker som fick mig att sälja min gamla iPhone",
                body=[],
                visual_type="person_far",
            )
            render_slide(
                output_path=body_path,
                position=1,
                kind="body",
                heading="1. jag slutade skjuta upp det",
                body=[
                    "mobilen blev bara liggande och tappade värde",
                    "så jag började med att jämföra bud",
                ],
                visual_type="object",
            )

            for output_path in (cover_path, body_path):
                self.assertTrue(output_path.exists())
                with Image.open(output_path) as image:
                    self.assertEqual(image.size, CANVAS_SIZE)
                    self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()
