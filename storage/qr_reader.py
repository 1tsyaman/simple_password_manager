from PIL import Image
from zxingcpp import read_barcode

from core.errors import (
	ImageOpenError,
	QRDecodeError,
	log
)

"""
	@raises:
		- ImageOpenError
		- QRDecodeError

"""
def read_qr_code(image_path: str) -> str:
	try:
		image = Image.open(image_path)
	except Exception as e:
		log(
			message=f"Something went wrong while openning the image {image_path}",
			error=e
		)

		raise ImageOpenError

	result = read_barcode(image)

	if result is not None:
		return result.text

	raise QRDecodeError