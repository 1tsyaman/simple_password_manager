from collections.abc import Callable

from kivy.clock import Clock
from kivy.utils import platform

from core.errors import (
	ImageOpenError,
	QRDecodeError,
	log
)


if platform == "android":
	from jnius import (
		autoclass,
		cast,
		java_method,
		PythonJavaClass
	)

	PythonActivity = autoclass("org.kivy.android.PythonActivity")
	GmsBarcodeScanning = autoclass(
		"com.google.mlkit.vision.codescanner.GmsBarcodeScanning"
	)
	GmsBarcodeScannerOptionsBuilder = autoclass(
		"com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions$Builder"
	)
	Barcode = autoclass(
		"com.google.mlkit.vision.barcode.common.Barcode"
	)

	_active_listeners = []


	class _SuccessListener(PythonJavaClass):
		__javainterfaces__ = [
			"com/google/android/gms/tasks/OnSuccessListener"
		]
		__javacontext__ = "app"

		def __init__(
			self,
			callback: Callable[[str], None]
		):
			super().__init__()
			self.callback = callback

		@java_method("(Ljava/lang/Object;)V")
		def onSuccess(self, result):
			barcode = cast(
				"com.google.mlkit.vision.barcode.common.Barcode",
				result
			)

			uri = barcode.getRawValue()

			if uri is not None:
				Clock.schedule_once(
					lambda *_: self.callback(uri)
				)

			_active_listeners.clear()


	class _FailureListener(PythonJavaClass):
		__javainterfaces__ = [
			"com/google/android/gms/tasks/OnFailureListener"
		]
		__javacontext__ = "app"

		def __init__(
			self,
			callback: Callable[[object], None] | None
		):
			super().__init__()
			self.callback = callback

		@java_method("(Ljava/lang/Exception;)V")
		def onFailure(self, exception):
			log(
				message="Something went wrong while scanning the QR code",
				error=exception
			)

			if self.callback is not None:
				Clock.schedule_once(
					lambda *_: self.callback(exception)
				)

			_active_listeners.clear()


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
		raise NotImplementedError(
			"Image-based QR decoding is not supported on Android"
		)

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


def read_qr_code_from_camera(
	callback: Callable[[str], None],
	error_callback: Callable[[object], None] | None = None
):
	if platform != "android":
		raise NotImplementedError(
			"Camera QR scanning is only supported on Android"
		)

	options = (
		GmsBarcodeScannerOptionsBuilder()
		.setBarcodeFormats(Barcode.FORMAT_QR_CODE)
		.enableAutoZoom()
		.build()
	)

	scanner = GmsBarcodeScanning.getClient(
		PythonActivity.mActivity,
		options
	)

	success_listener = _SuccessListener(callback)
	failure_listener = _FailureListener(error_callback)

	_active_listeners.extend(
		(success_listener, failure_listener)
	)

	task = scanner.startScan()

	task.addOnSuccessListener(success_listener)
	task.addOnFailureListener(failure_listener)
