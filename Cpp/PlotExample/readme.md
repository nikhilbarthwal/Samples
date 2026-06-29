=
How to build MatplotPlusPlus, with QT

After that, create a C++ example which display a graph of a Sin wave with a slider that adjusts its frequency in realtime. Also create a associated CMakeLists.txt file.
___

Good call  Qt fits this cleanly, and the only piece that actually has to change is the windowing/UI layer. Matplot++ keeps its job (render the sine wave to a PNG); Qt replaces SFML + ImGui entirely. Let me confirm the current Ubuntu Qt6 packaging before writing the steps.Confirmed: on Ubuntu 24.04, `qt6-base-dev` provides Qt6 Widgets plus its CMake config, so `find_package(Qt6 COMPONENTS Widgets)` works out of the box  no source build needed for Qt. That simplifies things a lot: the only library you still compile from source is Matplot++.

Here's what changes from the previous solution. SFML and ImGui-SFML are gone entirely (skip their build steps). Matplot++ stays exactly as before  it still renders the sine wave to a PNG. Qt now owns the window: a `QLabel` displays the PNG via `QPixmap`, and a `QSlider` drives the frequency. One wrinkle worth knowing up front: `QSlider` is integer-only, so the code maps an int range onto the fractional frequency (slider value / 100 -> 0.1010.00 Hz).

## 1. Dependencies

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake git pkg-config \
  qt6-base-dev \
  libpng-dev libjpeg-dev zlib1g-dev \
  gnuplot
```

`qt6-base-dev` pulls in Qt Widgets/Gui/Core and the build tools (moc/uic). `gnuplot` is still Matplot++'s runtime renderer. PNG decoding is built into Qt Gui, so no extra image plugin is needed.

## 2. Build Matplot++ as a shared library (unchanged)

This is identical to before  if you already did it, skip ahead:

```bash
git clone --depth 1 https://github.com/alandefreitas/matplotplusplus.git
cmake -S matplotplusplus -B matplotplusplus/build \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=ON \
  -DMATPLOTPP_BUILD_SHARED_LIBS=ON \
  -DMATPLOTPP_BUILD_EXAMPLES=OFF \
  -DMATPLOTPP_BUILD_TESTS=OFF \
  -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build matplotplusplus/build -j"$(nproc)"
sudo cmake --install matplotplusplus/build
sudo ldconfig
```

## 3. The Qt version of the example and its CMakeLists.txt## 4. Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
./build/sine_wave_qt
```

It writes `sine_plot.png` into the working directory, so run it from a writable folder on a machine with a display.

## Notes on the Qt-specific bits

The biggest behavioral difference from the SFML/ImGui version is the integer slider. `QSlider` only emits integer values, so the 101000 range is divided by 100 to get 0.1010.00 Hz. Widening the range or the divisor gives finer steps. The `valueLabel` shows the live value so it doesn't feel like a mystery dial.

For responsiveness, the same gnuplot-latency caveat applies, and it's slightly more visible here because `renderSineToPng` runs on Qt's GUI thread  a slow render briefly blocks event processing. Two easy fixes, in order of effort. The cheap one is to re-render only when you release the handle: connect to `QSlider::sliderReleased` (a no-argument signal) instead of `valueChanged`, reading `slider->value()` inside the slot. The slider then glides freely and the plot updates once you let go. The more thorough fix is to push `renderSineToPng` onto a `QThread` or `QtConcurrent::run`, deliver the finished `QPixmap` back via a queued signal, and coalesce rapid changes with a short `QTimer` debounce so you never queue more renders than you can draw.

And as before, if you want genuinely smooth per-frame animation rather than the image round-trip, the native route is **QtCharts** (`find_package(Qt6 COMPONENTS Charts)`, package `qt6-charts-dev`): feed a `QLineSeries` recomputed each time the slider moves and it redraws instantly, no gnuplot in the loop. I kept Matplot++ here since it's the library you're building the solution around, but that's the swap to make if the PNG latency bothers you.

___

### main.cpp
```cpp
// main.cpp
//
// Sine line + red cosine scatter (Matplot++) shown in a Qt window, with a
// QSlider for frequency. The plot fills the entire window and is re-rendered
// at the current widget size on resize, so it stays crisp instead of being
// upscaled.
//
// NOTE: Matplot++'s save() returns before gnuplot finishes writing the PNG, so
// loadPlotPixmap() waits until the file is a complete PNG before loading it
// (otherwise libpng reports "Read Error" on a truncated file).

#include <QApplication>
#include <QByteArray>
#include <QElapsedTimer>
#include <QFile>
#include <QHBoxLayout>
#include <QImage>
#include <QLabel>
#include <QPixmap>
#include <QResizeEvent>
#include <QSize>
#include <QSizePolicy>
#include <QSlider>
#include <QString>
#include <QThread>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>
#include <Qt>

#include <matplot/matplot.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <functional>
#include <string>
#include <system_error>
#include <vector>

namespace {

// Render a sine line + red cosine scatter at the requested pixel size.
bool renderSineToPng(double frequencyHz, const std::string& outPath,
                     std::size_t widthPx, std::size_t heightPx) {
    using namespace matplot;

    std::error_code ec;
    std::filesystem::remove(outPath, ec);  // ignore "didn't exist"

    const std::vector<double> x = linspace(0.0, 2.0, 2000);
    std::vector<double> y(x.size());
    for (std::size_t i = 0; i < x.size(); ++i) {
        y[i] = std::sin(2.0 * pi * frequencyHz * x[i]);
    }

    auto f = figure(true);  // quiet mode: no gnuplot window
    f->backend()->run_command("unset warnings");   // <-- add this line
    f->size(widthPx, heightPx);

    // Cosine sampled coarsely so the scatter markers read as distinct dots.
    const std::vector<double> xs = linspace(0.0, 2.0, 80);
    std::vector<double> yc(xs.size());
    for (std::size_t i = 0; i < xs.size(); ++i) {
        yc[i] = std::cos(2.0 * pi * frequencyHz * xs[i]);
    }

    auto ax = f->current_axes();

    ax->plot(x, y)->line_width(2);  // sine line

    ax->hold(on);                   // overlay the cosine scatter in red
    ax->scatter(xs, yc)
        ->marker_color("red")
        .marker_face_color("red")
        .marker_size(7);
    ax->hold(off);

    ax->title("sin (line) + cos (scatter)   |   f = " +
              std::to_string(frequencyHz) + " Hz");
    ax->xlabel("t (s)");
    ax->ylabel("amplitude");
    ax->xlim({-2, 3});
    ax->ylim({-1.2, 1.2});
    ax->grid(true);
    matplot::legend({"sin", "cos"});

    f->save(outPath);  // asynchronous w.r.t. gnuplot's actual file write
    return true;
}

// A complete PNG ends with the 12-byte IEND chunk.
bool pngIsComplete(const QString& path) {
    static const QByteArray kIend =
        QByteArray::fromHex("0000000049454e44ae426082");
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly) || file.size() < kIend.size()) {
        return false;
    }
    file.seek(file.size() - kIend.size());
    return file.read(kIend.size()) == kIend;
}

// Wait (up to timeoutMs) until gnuplot has written a full, loadable PNG.
QPixmap loadPlotPixmap(const QString& path, int timeoutMs = 4000) {
    QElapsedTimer timer;
    timer.start();
    while (timer.elapsed() < timeoutMs) {
        if (pngIsComplete(path)) {
            QImage img;
            if (img.load(path, "PNG")) {
                return QPixmap::fromImage(img);
            }
        }
        QThread::msleep(10);
    }
    return {};
}

// QWidget that reports resize events via a callback (no Q_OBJECT needed).
class PlotWindow : public QWidget {
public:
    using QWidget::QWidget;
    std::function<void(QSize)> onResize;

protected:
    void resizeEvent(QResizeEvent* event) override {
        QWidget::resizeEvent(event);
        if (onResize) {
            onResize(event->size());
        }
    }
};

}  // namespace

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);

    const std::string kPlotPath = "sine_plot.png";
    const int kSliderMin = 10;    // 0.10 Hz
    const int kSliderMax = 1000;  // 10.00 Hz

    PlotWindow window;
    window.setWindowTitle("Matplot++ + Qt");

    // The plot label fills all available space.
    auto* plotLabel = new QLabel(&window);
    plotLabel->setAlignment(Qt::AlignCenter);
    plotLabel->setMinimumSize(200, 150);
    plotLabel->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);

    auto* caption = new QLabel("Frequency (Hz):", &window);
    auto* slider = new QSlider(Qt::Horizontal, &window);
    slider->setRange(kSliderMin, kSliderMax);
    slider->setValue(100);  // 1.00 Hz
    auto* valueLabel = new QLabel(&window);
    valueLabel->setMinimumWidth(64);

    auto* controls = new QHBoxLayout;
    controls->setContentsMargins(8, 4, 8, 4);
    controls->addWidget(caption);
    controls->addWidget(slider, /*stretch=*/1);
    controls->addWidget(valueLabel);

    auto* layout = new QVBoxLayout(&window);
    layout->setContentsMargins(0, 0, 0, 0);  // plot goes edge-to-edge
    layout->setSpacing(0);
    layout->addWidget(plotLabel, /*stretch=*/1);
    layout->addLayout(controls);

    // Render the plot at the label's current pixel size and display it.
    auto renderAndShow = [&]() {
        const double freq = slider->value() / 100.0;
        valueLabel->setText(QString::asprintf("%.2f", freq));

        const qreal dpr = window.devicePixelRatioF();
        const auto w = static_cast<std::size_t>(
            std::max(1, static_cast<int>(plotLabel->width() * dpr)));
        const auto h = static_cast<std::size_t>(
            std::max(1, static_cast<int>(plotLabel->height() * dpr)));

        renderSineToPng(freq, kPlotPath, w, h);

        QPixmap pix = loadPlotPixmap(QString::fromStdString(kPlotPath));
        if (!pix.isNull()) {
            pix.setDevicePixelRatio(dpr);  // crisp on HiDPI
            plotLabel->setPixmap(pix);
        } else {
            plotLabel->setText("Could not load the plot (check gnuplot/PNG).");
        }
    };

    // Slider: re-render immediately for the new frequency.
    QObject::connect(slider, &QSlider::valueChanged, &window,
                     [&](int) { renderAndShow(); });

    // Resize: debounce so we re-render once, after the resize settles.
    auto* resizeTimer = new QTimer(&window);
    resizeTimer->setSingleShot(true);
    QObject::connect(resizeTimer, &QTimer::timeout, &window,
                     [&]() { renderAndShow(); });
    window.onResize = [resizeTimer](QSize) { resizeTimer->start(150); };

    window.resize(1000, 640);
    window.show();
    renderAndShow();  // initial render now that the label has a real size
    return app.exec();
}
```

### CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.16)
project(SineWaveQt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Let CMake run Qt's meta-object / resource / UI compilers automatically.
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Qt6 comes from apt (system path) and Matplot++ from /usr/local; both are on
# CMake's default search path. If you installed Matplot++ to ~/.local instead,
# uncomment:
#
# list(APPEND CMAKE_PREFIX_PATH "$ENV{HOME}/.local")

find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(Matplot++ REQUIRED)

add_executable(sine_wave_qt main.cpp)

target_link_libraries(sine_wave_qt
    PRIVATE
        Qt6::Widgets          # pulls in Qt Gui + Core transitively
        Matplot++::matplot
)
```
___

Here's the CMakeLists.txt for your library. The key thing to know up front: `find_package(library)` can't work from a CMakeLists alone  it needs a tiny config template installed alongside the library, so I'm giving you both files. Put them next to your `library.cpp` and `library.h`.Your project folder should look like this:

```
library/
 CMakeLists.txt
 libraryConfig.cmake.in
 library.cpp
 library.h
```

Build and install:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build build -j"$(nproc)"
sudo cmake --install build
sudo ldconfig
```

After that, any future project uses it with two lines:

```cmake
find_package(library REQUIRED)
target_link_libraries(myapp PRIVATE library::library)
```

and includes your header as `#include <library/library.h>`.

Two decisions you need to confirm against your actual code, both flagged in the comments:

The **Qt components** in `find_package(Qt6 ... COMPONENTS Widgets)` must match what your code uses. If `library.h`/`library.cpp` only need `Core`, or also need `Charts`, `Gui`, etc., edit that line  and keep the same component list in `libraryConfig.cmake.in`, since the config has to re-find Qt for your consumers (Qt is in your public header, so it's a `PUBLIC` dependency).

Whether **Matplot++ is PRIVATE or PUBLIC** depends on your header. I assumed it's an implementation detail used only in `library.cpp`, so it's `PRIVATE`  consumers never see it, and `libmatplot.so` is pulled in automatically at runtime. But if `library.h` itself `#include`s `<matplot/matplot.h>`, then it leaks into your public interface: move Matplot++ to `PUBLIC` in `target_link_libraries`, and uncomment the `find_dependency(Matplot++)` line in the config template.

One Windows note (ignore if you're Linux-only): the generated `library_export.h` is installed for you, but to actually export symbols on Windows you must annotate your public classes/functions with the `LIBRARY_EXPORT` macro  `#include "library_export.h"` in `library.h`, then write `class LIBRARY_EXPORT MyClass`. On Linux this is optional since symbols are visible by default, which is why it works without touching your header today.

___

```cmake
cmake_minimum_required(VERSION 3.16)
project(library VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Qt code generators: moc (for Q_OBJECT), uic (.ui files), rcc (.qrc files).
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

include(GNUInstallDirs)
include(GenerateExportHeader)
include(CMakePackageConfigHelpers)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
# Change the Qt components to whatever your code actually uses
# (e.g. Core Gui Widgets Charts). Widgets pulls in Core + Gui transitively.
find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(Matplot++ REQUIRED)

# ---------------------------------------------------------------------------
# The shared library
# ---------------------------------------------------------------------------
add_library(library SHARED
    library.cpp
    library.h          # listed so AUTOMOC processes any Q_OBJECT in it
)
add_library(library::library ALIAS library)   # for in-tree use / consistency

# Generates library_export.h defining the LIBRARY_EXPORT macro
# (dllexport/dllimport on Windows; visibility attributes elsewhere).
generate_export_header(library
    EXPORT_FILE_NAME ${CMAKE_CURRENT_BINARY_DIR}/library_export.h
)

target_include_directories(library
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>            # library_export.h
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/library>
)

# Qt appears in your public header -> PUBLIC (consumers need it).
# Matplot++ is assumed to be an implementation detail used only in library.cpp
# -> PRIVATE. If library.h #includes <matplot/matplot.h>, move Matplot++ to
# PUBLIC below AND uncomment the find_dependency line in libraryConfig.cmake.in.
target_link_libraries(library
    PUBLIC  Qt6::Widgets
    PRIVATE Matplot++::matplot
)

set_target_properties(library PROPERTIES
    VERSION     ${PROJECT_VERSION}
    SOVERSION   ${PROJECT_VERSION_MAJOR}
    EXPORT_NAME library
)

# ---------------------------------------------------------------------------
# Install the library and its headers
# ---------------------------------------------------------------------------
install(TARGETS library
    EXPORT  libraryTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(FILES
    library.h
    ${CMAKE_CURRENT_BINARY_DIR}/library_export.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/library
)

# ---------------------------------------------------------------------------
# Export an importable CMake package so consumers can: find_package(library)
# ---------------------------------------------------------------------------
install(EXPORT libraryTargets
    FILE        libraryTargets.cmake
    NAMESPACE   library::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/library
)

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/libraryConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/libraryConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/library
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/libraryConfigVersion.cmake
    VERSION       ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)
install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/libraryConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/libraryConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/library
)
```
___

```cmake
@PACKAGE_INIT@

include(CMakeFindDependencyMacro)

# Qt is a PUBLIC dependency (it appears in your installed header), so consumers
# need the Qt targets to exist. Keep these components in sync with the
# find_package(Qt6 ...) line in CMakeLists.txt.
find_dependency(Qt6 COMPONENTS Widgets)

# Matplot++ is PRIVATE by default (used only inside the .so), so consumers do
# NOT need it. Uncomment ONLY if library.h includes Matplot++ headers and you
# moved Matplot++ to PUBLIC in target_link_libraries():
# find_dependency(Matplot++)

include("${CMAKE_CURRENT_LIST_DIR}/libraryTargets.cmake")

check_required_components(library)
```

What each part does:

`@PACKAGE_INIT@` is a placeholder that `configure_package_config_file()` replaces at build time with boilerplate that sets up path helpers and makes the file relocatable, so the installed package works regardless of where the prefix ends up.

`find_dependency(Qt6 COMPONENTS Widgets)` re-resolves your public dependency on the consumer's machine. Because Qt appears in your public header, a consumer linking `library::library` must have the `Qt6::Widgets` target available  `find_dependency` is the config-file equivalent of `find_package`, but it also propagates `REQUIRED`/`QUIET` correctly and aborts the consumer's configure cleanly if Qt is missing.

The commented `find_dependency(Matplot++)` is there for the case where Matplot++ stops being a private implementation detail (i.e., your header includes `<matplot/matplot.h>`); uncomment it only if you also flip Matplot++ to `PUBLIC` in `target_link_libraries`.

`include(.../libraryTargets.cmake)` pulls in the file generated by `install(EXPORT ...)`, which actually defines the imported `library::library` target with its real installed paths, link libraries, and include directories.

`check_required_components(library)` validates any components a consumer requested via `find_package(library COMPONENTS ...)`. You don't expose components, so it's effectively a no-op, but `configure_package_config_file` expects it and it's standard hygiene.

The one line that's environment-specific is the `find_dependency` call  keep its component list identical to the `find_package(Qt6 ...)` line in your `CMakeLists.txt`, or a consumer could configure your package successfully yet fail to link.
