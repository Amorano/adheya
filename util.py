"""."""

import math
import numpy as np
from PIL import Image
from dearpygui import core

def pil_to_tex(handle):
	"""."""
	tex = []
	for i in range(0, handle.height):
		for j in range(0, handle.width):
			tex.extend(handle.getpixel((j, i)))
	return tex

def np_to_tex(data):
	"""."""
	return np.repeat(np.ndarray.flatten(data) * 100, 4)

def points_to_box(points):
	"""."""
	min_x = math.floor(points[:, 0].min())
	min_y = math.floor(points[:, 1].min())
	max_x = math.floor(points[:, 0].max())
	max_y = math.floor(points[:, 1].max())
	return (min_x, min_y, max_x, max_y)

def makeImage(imageFile: str, sliceX: int, sliceY: int):
	"""Slice an imagefile into X by Y chunks."""
	img = Image.open(imageFile).convert('RGBA')
	height = int(img.height / sliceY)
	width = int(img.width / sliceX)

	index = 0
	cap = sliceY * sliceX - 1
	for y in range(sliceY):
		y1 = y * height
		for x in range(sliceX):
			x1 = x * width

			tile = img.copy().crop((x1, y1, x1 + width, y1 + height))
			if index == cap:
				tile = Image.new('RGBA', (width, height))
			data = np.array(tile).ravel()
			core.add_texture(f"image-{index}", data, width, height)
			index += 1

def children(parent, recurse=True):
	if not isinstance(parent, list):
		parent = [parent]
	ret = []
	for p in parent:
		omni = core.get_item_children(p)
		ret.extend(omni)
		if recurse:
			ret.extend(children(omni))
	return ret
