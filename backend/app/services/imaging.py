"""Pre-check before spending an AI call: a bad photo should be re-uploaded, not guessed at."""
import io

from PIL import Image, ImageFilter, ImageStat

MIN_SIDE = 400
DARK, BRIGHT = 50, 250
SHARP_MIN = 450.0  # variance of the edge map; tuned on synthetic samples only, re-tune on real phone photos

TIPS = ["Place the page flat in good light", "Include the whole page, no cut-off edges",
        "Hold the phone steady and avoid shadows"]


def quality_issues(data: bytes) -> list[str]:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        return ["The file could not be opened as an image"]
    issues = []
    if min(img.size) < MIN_SIDE:
        issues.append("The photo is too small")
    gray = img.convert("L")
    gray.thumbnail((1000, 1000))
    mean = ImageStat.Stat(gray).mean[0]
    if mean < DARK:
        issues.append("The photo is too dark")
    elif mean > BRIGHT:
        issues.append("The photo is washed out")
    if ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).var[0] < SHARP_MIN:
        issues.append("The photo is blurry")
    return issues
