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

