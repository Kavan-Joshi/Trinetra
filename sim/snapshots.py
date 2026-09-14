from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLORS = {
    "Black": (32, 34, 40), "White": (235, 238, 240), "Grey": (120, 126, 132),
    "Silver": (190, 196, 200), "Red": (190, 42, 48), "Blue": (40, 80, 160),
    "Yellow": (232, 190, 60), "Orange": (230, 140, 50),
}

W, H = 640, 360


def _fonts():
    return ImageFont.load_default(16), ImageFont.load_default(11)


def render_snapshot(path: Path, *, spec, ts) -> None:
    img = Image.new("RGB", (W, H), (18, 24, 32))
    d = ImageDraw.Draw(img)
    font_l, font_s = _fonts()

    d.rectangle([0, 268, W, 342], fill=(40, 44, 52))
    for x in range(0, W, 44):
        d.rectangle([x, 302, x + 22, 306], fill=(214, 214, 120))

    d.rectangle([0, 0, W, 26], fill=(10, 14, 20))
    d.text((8, 5), f"TRINETRA EDGE  |  {spec.camera_id}", font=font_l, fill=(120, 200, 255))
    stamp = ts.strftime("%d %b %Y  %H:%M:%S") + " IST"
    d.text((W - 158, 8), stamp, font=font_s, fill=(200, 200, 200))

    if spec.kind == "vehicle":
        body_color = COLORS.get(spec.color, (120, 126, 132))
        d.rounded_rectangle([168, 244, 472, 330], radius=16, fill=body_color, outline=(226, 226, 226), width=2)
        d.rounded_rectangle([214, 254, 330, 292], radius=8, fill=(58, 62, 72))
        d.rounded_rectangle([344, 254, 438, 292], radius=8, fill=(58, 62, 72))
        plate_text = (spec.plate or "").replace("-", " ")
        d.rounded_rectangle([252, 300, 388, 332], radius=4, fill=(245, 245, 245), outline=(8, 8, 8), width=2)
        d.text((262, 308), plate_text, font=font_l, fill=(12, 12, 12))
        d.text((168, 216), f"{spec.vehicle_class.upper()}   {spec.speed_kmh:.0f} km/h   {spec.direction}", font=font_s, fill=(230, 230, 230))
        if spec.plate_confidence:
            d.text((168, 232), f"ANPR confidence {spec.plate_confidence:.0%}  |  {spec.color}", font=font_s, fill=(140, 220, 160))
    elif spec.kind == "person":
        for cx in (220, 280, 360, 430):
            d.ellipse([cx - 16, 210, cx + 16, 242], fill=(60, 66, 78), outline=(210, 210, 210))
            d.rounded_rectangle([cx - 20, 246, cx + 20, 320], radius=10, fill=(50, 56, 68), outline=(210, 210, 210))
        d.rectangle([0, 236, W, 254], fill=(170, 40, 46))
        d.text((12, 240), "CROWD ANOMALY", font=font_l, fill=(255, 255, 255))
    else:
        d.rounded_rectangle([280, 262, 360, 322], radius=8, fill=(120, 84, 52), outline=(220, 210, 190), width=2)
        d.line([280, 262, 360, 262], fill=(80, 56, 34), width=6)
        d.rectangle([0, 236, W, 254], fill=(170, 40, 46))
        d.text((12, 240), "UNATTENDED OBJECT", font=font_l, fill=(255, 255, 255))

    if spec.attributes.get("anomaly"):
        d.text((12, 180), str(spec.attributes.get("anomaly_detail", ""))[:70], font=font_s, fill=(255, 190, 190))

    d.rectangle([0, H - 18, W, H], fill=(10, 14, 20))
    d.text((8, H - 15), "Federated edge gateway — event evidence frame", font=font_s, fill=(120, 140, 160))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
