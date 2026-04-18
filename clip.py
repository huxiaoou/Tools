import os
import argparse
from PIL import Image


def parse_args():
    arg_parser = argparse.ArgumentParser(description="CLIP")
    arg_parser.add_argument("--src", type=str, required=True, help="Path to the source directory")
    arg_parser.add_argument("--dst", type=str, required=True, help="Path to the destination directory")
    arg_parser.add_argument("--format", type=str, default="png", help="Output image format (default: png)")
    arg_parser.add_argument(
        "--box", type=int, nargs=4, required=True, help="Bounding box for clipping (left, upper, right, lower)"
    )

    return arg_parser.parse_args()


def clip_image(image_path: str, box: tuple[int, int, int, int], output_path: str, output_format: str):
    original = Image.open(image_path)
    cropped_image = original.crop(box)
    cropped_image.save(output_path, format=output_format)
    print(f"Processing {image_path} and saving to {output_path}")
    return


def main():
    args = parse_args()
    print(f"Source directory: {args.src}")
    print(f"Destination directory: {args.dst}")
    print(f"Output format: {args.format}")

    if not os.path.exists(args.src):
        print(f"Source directory {args.src} does not exist.")
        return

    if not os.path.exists(args.dst):
        os.makedirs(args.dst)

    for filename in os.listdir(args.src):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            src_path = os.path.join(args.src, filename)
            dst_path = os.path.join(args.dst, os.path.splitext(filename)[0] + "." + args.format)
            clip_image(src_path, tuple(args.box), dst_path, args.format)


if __name__ == "__main__":
    main()
