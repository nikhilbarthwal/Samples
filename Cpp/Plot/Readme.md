
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

### Check:
gnuplot -e "set terminal pngcairo size 400,300; set output 'test.png'; plot sin(x); unset output"
file test.png      # should print: PNG image data, 400 x 300, ...

### main.cpp
```cpp
// main.cpp
//
// Sine wave plot (Matplot++) displayed in a Qt window, with a QSlider that
// adjusts the frequency in real time.
//
// Pipeline: Matplot++ -> gnuplot writes a PNG -> Qt loads it into a QLabel.
//
// IMPORTANT: Matplot++'s save() returns before gnuplot (a separate process)
// has finished flushing the PNG to disk. Reading it too early gives libpng a
// truncated file ("libpng error: Read Error"). loadPlotPixmap() below waits
// until the file is a *complete* PNG before handing it to Qt.

#include <QApplication>
#include <QByteArray>
#include <QElapsedTimer>
#include <QFile>
#include <QHBoxLayout>
#include <QImage>
#include <QLabel>
#include <QPixmap>
#include <QSlider>
#include <QString>
#include <QThread>
#include <QVBoxLayout>
#include <QWidget>
#include <Qt>

#include <matplot/matplot.h>

#include <cmath>
#include <cstddef>
#include <filesystem>
#include <string>
#include <system_error>
#include <vector>

namespace {

// Render a sine wave of the given frequency to `outPath` (PNG).
// The stale file is removed first so a later completeness check can't pass on
// the previous render's image.
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
    f->size(widthPx, heightPx);

    auto ax = f->current_axes();
    ax->plot(x, y)->line_width(2);
    ax->title("Sine wave   |   f = " + std::to_string(frequencyHz) + " Hz");
    ax->xlabel("t (s)");
    ax->ylabel("amplitude");
    ax->ylim({-1.2, 1.2});
    ax->grid(true);

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
    return {};  // timed out -> null pixmap
}

}  // namespace

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);

    const std::string kPlotPath = "sine_plot.png";
    const std::size_t kPlotW = 900;
    const std::size_t kPlotH = 500;

    // Slider integer range -> frequency = value / 100.0
    const int kSliderMin = 10;    // 0.10 Hz
    const int kSliderMax = 1000;  // 10.00 Hz

    QWidget window;
    window.setWindowTitle("Matplot++ + Qt");

    auto* plotLabel = new QLabel(&window);
    plotLabel->setAlignment(Qt::AlignCenter);
    plotLabel->setMinimumSize(static_cast<int>(kPlotW), static_cast<int>(kPlotH));

    auto* caption = new QLabel("Frequency (Hz):", &window);

    auto* slider = new QSlider(Qt::Horizontal, &window);
    slider->setRange(kSliderMin, kSliderMax);
    slider->setValue(100);  // 1.00 Hz

    auto* valueLabel = new QLabel(&window);
    valueLabel->setMinimumWidth(64);

    auto* controls = new QHBoxLayout;
    controls->addWidget(caption);
    controls->addWidget(slider, /*stretch=*/1);
    controls->addWidget(valueLabel);

    auto* layout = new QVBoxLayout(&window);
    layout->addWidget(plotLabel, /*stretch=*/1);
    layout->addLayout(controls);

    auto refresh = [&](int sliderValue) {
        const double freq = sliderValue / 100.0;
        valueLabel->setText(QString::asprintf("%.2f", freq));

        renderSineToPng(freq, kPlotPath, kPlotW, kPlotH);

        const QPixmap pix = loadPlotPixmap(QString::fromStdString(kPlotPath));
        if (!pix.isNull()) {
            plotLabel->setPixmap(pix);
        } else {
            plotLabel->setText(
                "Could not load the plot.\n"
                "Check that gnuplot is installed with PNG support:\n"
                "  gnuplot -e \"set term pngcairo; set output 'x.png'; plot sin(x)\"");
        }
    };

    QObject::connect(slider, &QSlider::valueChanged, &window, refresh);

    refresh(slider->value());  // initial render

    window.resize(static_cast<int>(kPlotW) + 40, static_cast<int>(kPlotH) + 120);
    window.show();
    return app.exec();
}

```

### CMakeLists.txt
```text
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
