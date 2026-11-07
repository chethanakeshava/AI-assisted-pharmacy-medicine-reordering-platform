"""Generate FAKE prescription images for testing (no real patient data). Run from backend/."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

LINES = ["Dr. A. Sample, MBBS  (FAKE - TEST ONLY)", "Reg. No: WB-00000", "Patient: Test Patient   Age: 62", "",
         "Rx", "1. Tab Metformin 500 mg   1-0-1   x 60", "2. Tab Telmisartan 40 mg   0-0-1   x 30", "", "Sign: A. Sample"]


def page(size=(1000, 1300)):
    img = Image.new("RGB", size, (236, 233, 226))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default(size=34)
    for i, line in enumerate(LINES):
        d.text((70, 90 + i * 90), line, fill="black", font=f)
    d.line((60, 60, 940, 60), fill="black", width=3)
    return img


if __name__ == "__main__":
    base = page()
    base.save("sample_prescriptions/rx_clear.png")
    base.filter(ImageFilter.GaussianBlur(9)).save("sample_prescriptions/rx_blurry.png")
    base.filter(ImageFilter.GaussianBlur(3)).save("sample_prescriptions/rx_slightly_soft.png")
    Image.eval(base, lambda v: int(v * 0.12)).save("sample_prescriptions/rx_dark.png")
    base.resize((300, 390)).save("sample_prescriptions/rx_tiny.png")
    print("done")
