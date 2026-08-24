# Simple Password Manager

A small password manager written in Python using Kivy/KivyMD for the GUI.

The project can be run directly on desktop and can also be packaged as an Android application with Buildozer / python-for-android.

> **Note:** Android packaging currently requires a few workarounds for some native Python dependencies, especially `argon2-cffi` and `cryptography`. The steps below document the setup that produced a working `arm64-v8a` debug APK.

## Requirements

### Desktop

- Python **3.13**
- pip
- A virtual environment

Python 3.13.15 is known to work with this project.

Create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Install the desktop dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

## Building for Android

The Android build described here was tested on Ubuntu using:

- Python 3.13.15
- Kivy 2.3.1
- KivyMD 2.0.0
- Buildozer
- python-for-android
- Android NDK r28c
- Android API 33
- Minimum Android API 24
- `arm64-v8a`

### 1. Install system dependencies

```bash
sudo apt update

sudo apt install -y \
    git zip unzip \
    openjdk-17-jdk \
    python3-pip python3-venv \
    autoconf automake libtool pkg-config \
    zlib1g-dev libffi-dev libssl-dev \
    cmake gettext \
    adb
```

If multiple Java versions are installed, make sure Java 17 is selected:

```bash
sudo update-alternatives --config java
sudo update-alternatives --config javac
```

### 2. Install Python 3.13.15

Using `pyenv` is recommended because the Android build is pinned to the same Python version:

```bash
pyenv install 3.13.15
```

Create a separate Buildozer environment:

```bash
~/.pyenv/versions/3.13.15/bin/python -m venv ~/.venvs/buildozer
source ~/.venvs/buildozer/bin/activate
```

Install Buildozer and python-for-android:

```bash
python -m pip install --upgrade pip
python -m pip install buildozer python-for-android
```

If the local python-for-android checkout later reports missing host modules such as `appdirs`, `sh`, `colorama`, or `jinja2`, update/reinstall python-for-android rather than installing dependencies one by one:

```bash
python -m pip install --upgrade python-for-android
```

### 3. Install Rust through rustup

`cryptography` contains Rust code and requires a Rust toolchain.

```bash
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

Verify:

```bash
which rustc
which cargo
which rustup
```

The preferred tools should be under:

```text
~/.cargo/bin/
```

If Ubuntu already provides `/bin/rustc` and the rustup installer refuses to continue:

```bash
RUSTUP_INIT_SKIP_PATH_CHECK=yes curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

### 4. Configure `buildozer.spec`

The important requirements are:

```ini
requirements = python3==3.13.15,hostpython3==3.13.15,kivy==2.3.1,kivymd,cryptography,argon2-cffi,pyotp,materialyoucolor==3.0.4,materialshapes,pycairo,pillow,exceptiongroup,asyncgui,asynckivy,android
```

The Android configuration used during development is:

```ini
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
```

NDK r28c is known to work with this setup.

Make sure the requirements line contains **only one** `requirements =` assignment. A malformed line can accidentally create package names such as `pyotprequirements` or even `=`.

### 5. Start the build

From the repository root:

```bash
buildozer -v android debug
```

The first build is slow because Buildozer/python-for-Android must download and compile Python, Kivy, OpenSSL, Cairo, Rust components, and other native libraries.

Do not run multiple Buildozer builds against the same `.buildozer` directory at the same time.

After a successful build, the APK should be available under:

```text
bin/
```

## Installing on a device

Enable **Developer options** and **USB debugging** on the Android device.

Check that ADB can see it:

```bash
adb devices
```

Then deploy and run:

```bash
buildozer android deploy run
```

Or build, deploy, and run in one command:

```bash
buildozer android debug deploy run
```

A debug build can normally update an already installed debug build as long as the application ID and signing key have not changed.

## Troubleshooting

### `ModuleNotFoundError: materialyoucolor`

Example:

```text
ModuleNotFoundError: No module named 'materialyoucolor'
```

KivyMD has runtime dependencies that are not necessarily pulled into the APK automatically.

Make sure the Android requirements include:

```text
materialyoucolor
materialshapes
pycairo
pillow
exceptiongroup
asyncgui
asynckivy
android
```

Rebuild without cleaning:

```bash
buildozer -v android debug
```

### Pixman download times out

Example:

```text
Downloading pixman source ...
<urlopen error timed out>
```

This is normally a download/network problem, not a compilation problem.

Test the source URL manually:

```bash
curl -I https://www.cairographics.org/releases/pixman-0.43.4.tar.gz
```

or:

```bash
wget https://www.cairographics.org/releases/pixman-0.43.4.tar.gz
```

If the URL is reachable, rerun Buildozer. Existing compiled components are normally reused.

Avoid `buildozer android clean` unless necessary.

### Buildozer tries to install `pyotprequirements`

Example:

```text
ERROR: No matching distribution found for pyotprequirements
ERROR: Invalid requirement: '='
```

The `requirements` line in `buildozer.spec` is malformed.

Replace the complete line with:

```ini
requirements = python3==3.13.15,hostpython3==3.13.15,kivy==2.3.1,kivymd,cryptography,argon2-cffi,pyotp,materialyoucolor==3.0.4,materialshapes,pycairo,pillow,exceptiongroup,asyncgui,asynckivy,android
```

### `rustup` was not found

Example:

```text
`rustup` was not found on host system
```

Install Rust through rustup:

```bash
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

If a system Rust installation already exists:

```bash
RUSTUP_INIT_SKIP_PATH_CHECK=yes curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

### `argon2-cffi` fails because `pycparser` is missing

A python-for-android Argon2 build may fail inside its host Python environment with:

```text
ModuleNotFoundError: No module named 'pycparser'
```

Install `pycparser` into python-for-android's generated host Python:

```bash
HOSTPY=".buildozer/android/platform/build-arm64-v8a/build/other_builds/hostpython3/desktop/hostpython3/native-build/root/usr/local/bin/python"

"$HOSTPY" -m ensurepip
"$HOSTPY" -m pip install pycparser
```

Then rerun:

```bash
buildozer -v android debug
```

Do not clean first.

The current python-for-android Argon2 recipe may build an older `argon2-cffi` release than the version used on desktop. This is controlled by the recipe rather than the normal pip requirement resolver.

### `cryptography` crashes with `PyExc_TypeError`

The APK may build successfully but crash immediately with:

```text
ImportError: dlopen failed: cannot locate symbol "PyExc_TypeError"
referenced by ".../cryptography/hazmat/bindings/_rust.abi3.so"
```

Check the Rust extension:

```bash
RUSTSO=$(find .buildozer/android/platform/build-arm64-v8a \
    -name '_rust.abi3.so' | head -1)

readelf -d "$RUSTSO" | grep -E 'NEEDED|python'
```

If `libpython3.13.so` is missing from `NEEDED`, verify the symbol:

```bash
PYLIB=$(find .buildozer/android/platform/build-arm64-v8a \
    -name 'libpython3.13.so' | head -1)

readelf -Ws "$PYLIB" | grep PyExc_TypeError
readelf -Ws "$RUSTSO" | grep PyExc_TypeError
```

A broken build typically shows:

```text
libpython3.13.so: GLOBAL ... PyExc_TypeError
_rust.abi3.so:   UND    ... PyExc_TypeError
```

#### Workaround

Create the generic Python library name expected by PyO3:

```bash
PYROOT="$PWD/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/arm64-v8a__ndk_target_24/python3/android-build"

ln -sf libpython3.13.so "$PYROOT/libpython3.so"
```

Then patch:

```text
.buildozer/android/platform/python-for-android/pythonforandroid/recipe.py
```

in the Rust recipe environment setup so that the generated `RUSTFLAGS` include the Python library directory and force the Python dependency to be retained:

```python
python_lib_dir = self.ctx.python_recipe.link_root(arch.arch)

env["RUSTFLAGS"] = env.get("RUSTFLAGS", "")
env["RUSTFLAGS"] += f" -Lnative={python_lib_dir}"
env["RUSTFLAGS"] += " -Clink-arg=-Wl,--no-as-needed"
env["RUSTFLAGS"] += f" -Clink-arg=-lpython{self.ctx.python_recipe.link_version}"
env["RUSTFLAGS"] += " -Clink-arg=-Wl,--as-needed"
```

If `RUSTFLAGS` is accessed using `+=` before initialization, the build fails with:

```text
KeyError: 'RUSTFLAGS'
```

which is why the `env.get("RUSTFLAGS", "")` initialization is required.

If the linker reports:

```text
ld.lld: error: unable to find library -lpython3
ld.lld: error: unable to find library -lpython3.13
```

the `-Lnative=...` path and the `libpython3.so` symlink above are missing or incorrect.

Rebuild:

```bash
buildozer -v android debug
```

Afterwards verify:

```bash
RUSTSO=$(find .buildozer/android/platform/build-arm64-v8a \
    -name '_rust.abi3.so' | head -1)

readelf -d "$RUSTSO" | grep -E 'NEEDED|python'
```

A corrected extension should list:

```text
Shared library: [libpython3.13.so]
```

This workaround modifies files under `.buildozer`, so deleting that directory or performing a full clean may remove it.

### `libpython3.14.so not found` appears in logcat

If the log immediately continues with:

```text
Loading library: python3.13
...
libpython3.13.so ... ok
```

then this is only python-for-android probing for another Python library. It is not the crash by itself.

Look for the later Python traceback.

### Suspicious `_cffi_backend...x86_64...so` warning

During the Argon2 installation you may see something similar to:

```text
_cffi_backend.cpython-313-x86_64-linux-gnu.so already exists
```

inside an `arm64-v8a` installation directory.

That is suspicious because native Android extensions should be built for ARM64.

Inspect it with:

```bash
find .buildozer/android/platform/build-arm64-v8a/build/python-installs/simplepasswordmanager/arm64-v8a \
    -maxdepth 1 -name '_cffi_backend*' -print -exec file {} \;
```

For the Android target, native shared objects should report an ARM/AArch64 architecture rather than x86-64.

If the application runs and Argon2 works, do not delete working build artifacts unnecessarily. If CFFI/Argon2 imports fail at runtime, investigate this file first.

## Android crash debugging

Clear the existing log:

```bash
adb logcat -c
```

Start the application and then inspect Python output:

```bash
adb logcat | grep -Ei "python|traceback|kivy|simplepasswordmanager|AndroidRuntime|FATAL"
```

A Python packaging/import problem normally appears as:

```text
Traceback (most recent call last):
...
ImportError: ...
```

The Android `WindowManager`, `SurfaceFlinger`, and activity-destroyed messages that follow are usually consequences of the Python process terminating, not the original cause.

## Build cache

Buildozer/python-for-android caches a large amount of native build output under:

```text
.buildozer/
```

For normal code changes and dependency additions, prefer:

```bash
buildozer -v android debug
```

without cleaning.

Use:

```bash
buildozer android clean
```

only when the cached native build state is genuinely incompatible, for example after major Python/NDK/architecture changes.

Cleaning can make the next build substantially slower and will also remove manual fixes made inside `.buildozer`.

## References

- Buildozer: https://github.com/kivy/buildozer
- python-for-android: https://github.com/kivy/python-for-android
- Kivy: https://kivy.org/
- KivyMD: https://kivymd.readthedocs.io/
