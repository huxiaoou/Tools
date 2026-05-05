#!/usr/bin/env python

from ast import main
import os
import argparse
import json
from enum import IntEnum
from PIL import Image
from husfort.qlog import define_logger, logger
from husfort.qutility import SFG, SFY
from dataclasses import dataclass, asdict


class LoopType(IntEnum):
    NONE = 0
    LINEAR = 1
    PINGPONG = 2


@dataclass
class AekaAnim:
    bgn: int
    stp: int
    loop: LoopType


@dataclass
class AekaLib:
    texture_path: str
    hframes: int
    vframes: int
    frame_duration: float
    animations: dict[str, AekaAnim]
    save_path: str


ANIM_LOOPMODE: dict[str, LoopType] = {
    "AttackA": LoopType.NONE,
    "AttackB": LoopType.NONE,
    "AttackC": LoopType.NONE,
    "Damage": LoopType.NONE,
    "Dash": LoopType.NONE,
    "Defeat": LoopType.NONE,
    "Evade": LoopType.NONE,
    "Guard": LoopType.NONE,
    "Idle": LoopType.PINGPONG,
    "Ready": LoopType.PINGPONG,
    "Skill": LoopType.PINGPONG,
    "Sleep": LoopType.PINGPONG,
    "Victory": LoopType.PINGPONG,
    "WeakIdle": LoopType.PINGPONG,
}

define_logger()


def parse_args():
    arg_parser = argparse.ArgumentParser("A program to generate sprite sheets")
    arg_parser.add_argument("src", type=str, help="src directory")
    arg_parser.add_argument(
        "--duration", type=float, default=0.04, help="frame duration for the sprite sheet (default: 0.04s)"
    )
    arg_parser.add_argument("--save", type=str, required=True, help="save path of the sprite_sheet")
    arg_parser.add_argument("--ncol", type=int, default=24, help="number of cols")
    arg_parser.add_argument("--shrink", type=float, default=1.0, help="the ratio to shrink")
    arg_parser.add_argument(
        "--width", type=int, default=None, help="if provided, will be used to set unit cell width (in pixel) for png"
    )
    arg_parser.add_argument(
        "--height", type=int, default=None, help="if provided, will be used to set unit cell height (in pixel) for png"
    )
    arg_parser.add_argument("--wsep", type=int, default=0, help="width separation between columns")
    arg_parser.add_argument("--hsep", type=int, default=0, help="height separation between rows")
    _args = arg_parser.parse_args()
    return _args


def get_pngs(src: str, reverse: bool = False) -> list[str]:
    ls = [file_path for file_path in os.listdir(src) if file_path.endswith(".png") or file_path.endswith(".PNG")]
    return sorted(ls, reverse=reverse)


def cal_nrow(tot_count: int, ncol_: int) -> int:
    _nrow, _remain = tot_count // ncol_, tot_count % ncol_
    if _remain > 0:
        _nrow += 1
    return _nrow


def get_png_size(p_path: str) -> tuple[int, int]:
    with Image.open(p_path) as _img:
        return _img.width, _img.height


def get_cell_width_height(args_width: int, args_height: int) -> tuple[int, int]:
    if args_width:
        if args_height:
            png_w, png_h = args_width, args_height
        else:
            png_w = png_h = args_width
    else:
        if args_height:
            png_w = png_h = args_height
        else:
            png_w, png_h = get_png_size(os.path.join(args.src, pngs[0]))
    return png_w, png_h


def get_image_size(png_w: int, png_h: int, ncol: int, nrow: int, wsep: int, hsep: int) -> tuple[int, int]:
    return (png_w + wsep) * ncol, (png_h + hsep) * nrow


def main_loop(
    merged_image: Image.Image,
    aeka_lib: AekaLib,
    src: str,
    pngs: list[str],
    ncol: int,
    png_w: int,
    png_h: int,
    wsep: int,
    hsep: int,
):
    curr_anim_name: str = ""
    for sn, png in enumerate(pngs):
        _, png_anim_name, _ = png[:-4].split("_")
        png_anim_name = png_anim_name.replace(" ", "")
        if png_anim_name != curr_anim_name:  # new animation starts
            if curr_anim_name in aeka_lib.animations:  # if the animation already exists, update the stp frame
                aeka_lib.animations[curr_anim_name].stp = sn
            curr_anim_name = png_anim_name  # update the current animation name
            aeka_lib.animations[curr_anim_name] = AekaAnim(
                bgn=sn, stp=sn, loop=ANIM_LOOPMODE.get(curr_anim_name, LoopType.NONE)
            )
        loc_col, loc_row = sn % ncol, sn // ncol
        png_path = os.path.join(src, png)
        with Image.open(png_path) as img:
            w, h = (png_w + wsep) * loc_col, (png_h + hsep) * loc_row
            merged_image.paste(img, box=(w, h))
            logger.info(f"{SFG(png_path)} is added at location({SFY(f'width={w:>6d}, height={h:>6d}')})")
    if curr_anim_name in aeka_lib.animations:  # update the stp frame for the last animation
        aeka_lib.animations[curr_anim_name].stp = png_count
    return


def shrink_image(merged_image: Image.Image, img_w: int, img_h: int, shrink_ratio: float) -> Image.Image:
    if shrink_ratio <= 1.0:
        logger.info(f"Shrinking sprite sheet to ration {shrink_ratio}")
        shrink_size = (int(img_w * shrink_ratio), int(img_h * shrink_ratio))
        merged_image = merged_image.resize(size=shrink_size)
    else:
        logger.warning(f"shrink ratio = {shrink_ratio}, which is greater than 1. And no shrinking is done")
    return merged_image


if __name__ == "__main__":
    args = parse_args()
    pngs = get_pngs(args.src)
    ncol = args.ncol
    if pngs:
        name = os.path.basename(args.save)
        name = name[:-4] if name.endswith(".png") else name
        aeka_lib = AekaLib(
            texture_path=f"res://assets/aekalib/{name}.png",
            hframes=ncol,
            vframes=cal_nrow(tot_count=len(pngs), ncol_=ncol),
            frame_duration=0.04,
            animations={},
            save_path=f"res://resources/aekalib/{name}.res",
        )

        png_count = len(pngs)
        nrow = cal_nrow(tot_count=png_count, ncol_=ncol)
        png_w, png_h = get_cell_width_height(args.width, args.height)
        img_w, img_h = get_image_size(png_w, png_h, ncol, nrow, args.wsep, args.hsep)
        merged_image = Image.new(mode="RGBA", size=(img_w, img_h))
        main_loop(
            merged_image=merged_image,
            aeka_lib=aeka_lib,
            src=args.src,
            pngs=pngs,
            ncol=ncol,
            png_w=png_w,
            png_h=png_h,
            wsep=args.wsep,
            hsep=args.hsep,
        )
        merged_image = shrink_image(merged_image, img_w, img_h, args.shrink)

        img_save_path = args.save if args.save.endswith(".png") else args.save + ".png"
        json_save_path = args.save.replace(".png", ".json") if args.save.endswith(".png") else args.save + ".json"

        merged_image.save(img_save_path)
        logger.info(f"The sprite is saved to {SFG(img_save_path)}")

        jdata = {name: asdict(aeka_lib)}
        with open(json_save_path, "w") as f:
            json.dump(jdata, f)
        logger.info(f"The animation data is saved to {SFG(json_save_path)}")
    else:
        print(f"There is no png available at {args.src}")
