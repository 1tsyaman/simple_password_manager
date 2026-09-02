from kivy.utils import platform

from core.errors import (
	ImageOpenError,
	QRDecodeError,
	log
)


if platform == "android":
	from jnius import autoclass

	BitmapFactory = autoclass("android.graphics.BitmapFactory")
	Rect = autoclass("android.graphics.Rect")
	BarcodeReader = autoclass("zxingcpp.BarcodeReader")

	barcode_reader = BarcodeReader()

else:
	from PIL import Image
	from zxingcpp import read_barcode


"""
	@raises:
		- ImageOpenError
		- QRDecodeError
"""
def read_qr_code(image_path: str) -> str:
	if platform == "android":
		return _read_qr_code_android(image_path)

	return _read_qr_code_desktop(image_path)


def _read_qr_code_desktop(image_path: str) -> str:
	try:
		image = Image.open(image_path)
	except Exception as e:
		log(
			message=f"Something went wrong while opening the image {image_path}",
			error=e
		)

		raise ImageOpenError

	result = read_barcode(image)

	if result is not None:
		return result.text

	raise QRDecodeError


def _read_qr_code_android(image_path: str) -> str:
	try:
		bitmap = BitmapFactory.decodeFile(image_path)

		if bitmap is None:
			raise ValueError("BitmapFactory could not decode image")
	except Exception as e:
		log(
			message=f"Something went wrong while opening the image {image_path}",
			error=e
		)

		raise ImageOpenError

	rect = Rect(
		0,
		0,
		bitmap.getWidth(),
		bitmap.getHeight()
	)

	results = barcode_reader.read(
		bitmap,
		rect,
		0
	)

	if results.size() > 0:
		return results.get(0).getText()

	raise QRDecodeError