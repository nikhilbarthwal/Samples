#include "histogram.h"
#include "common.h"

#include <QLabel>
#include <QPaintEvent>
#include <QPainter>
#include <QPalette>
#include <QPen>
#include <QSlider>
#include <QVBoxLayout>
#include <QWidget>

#include <algorithm>
#include <memory>
#include <set>
#include <vector>

using namespace std;


Histogram::counts Histogram::Data::Count(const int n) const
{
    counts result = Values;
    if (static_cast<int>(result.size()) > n)
        result.resize(n);
    else if (static_cast<int>(result.size()) < n)
        result.resize(n, 0.0f);
    return result;
}


Histogram::DynamicData::~DynamicData() = default;


class Plot
{
public:
    const string WindowTitle;
    const Histogram::Canvas Canvas;
    const float MinP;
    const float MaxP;
    const bool Slider;

    Plot(const Histogram::Canvas& canvas, const float minP, const float maxP):
        WindowTitle(canvas.Title), Canvas(canvas), MinP(minP), MaxP(maxP),
        Slider(minP != maxP) { }

    void Show() const;
    void Show(float) const;

    [[nodiscard]] virtual string Title(float parameter) const = 0;
    [[nodiscard]] virtual Histogram::DataFrame Get(float) const = 0;
    virtual ~Plot() = default;
};


class HistogramCanvas final : public QWidget
{
public:
    explicit HistogramCanvas(const Plot *histogram, QWidget *parent = nullptr):
        QWidget(parent), histogram(histogram), Bins(histogram->Canvas.Size)
    {
        setMinimumSize(640, 480);
        setAutoFillBackground(true);
        QPalette palette = this->palette();
        palette.setColor(QPalette::Window, QColor(252, 252, 252));
        setPalette(palette);
    }

    void SetParameter(float param)
    {
        parameter = param;
        update();
    }

protected:
    void paintEvent(QPaintEvent* /*event*/) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, true);

        const QRect plot_area = PlotArea();
        DrawBackground(painter);
        DrawGrid(painter, plot_area);
        DrawAxes(painter, plot_area);
        DrawHistograms(painter, plot_area);
        DrawLegend(painter, plot_area);
    }

private:
    [[nodiscard]] static float MinX()
        { return 0.0f; }

    [[nodiscard]] float MaxX() const
        { return static_cast<float>(histogram->Canvas.Size); }

    QRect PlotArea() const
    {
        return rect().adjusted(kPlotMarginLeft, kPlotMarginTop,
                -kPlotMarginRight, -kPlotMarginBottom);
    }

    float ToPixelX(const QRect &plot_area, float x) const
    {
        const float x_range = MaxX() - MinX();
        const float x_ratio =
                x_range == 0.0f ? 0.0f : (x - MinX()) / x_range;
        return plot_area.left() + x_ratio * plot_area.width();
    }

    float ToPixelY(const QRect &plot_area, float y) const
    {
        const float y_range = histogram->Canvas.MaxY - histogram->Canvas.MinY;
        const float y_ratio =
                y_range == 0.0f ? 0.0f : (y - histogram->Canvas.MinY) / y_range;
        return plot_area.bottom() - y_ratio * plot_area.height();
    }

    void DrawBackground(QPainter &painter) const
    {
        painter.fillRect(rect(), QColor(252, 252, 252));
        painter.fillRect(PlotArea(), Qt::white);
    }

    void DrawGrid(QPainter &painter, const QRect &plot_area) const
    {
        QPen grid_pen(QColor(220, 220, 220));
        grid_pen.setStyle(Qt::DotLine);
        painter.setPen(grid_pen);

        constexpr int kGridLines = 8;
        for (int i = 1; i < kGridLines; ++i)
        {
            const int x = plot_area.left()
                    + (plot_area.width() * i) / kGridLines;
            const int y = plot_area.top()
                    + (plot_area.height() * i) / kGridLines;
            painter.drawLine(x, plot_area.top(), x, plot_area.bottom());
            painter.drawLine(plot_area.left(), y, plot_area.right(), y);
        }
    }

    void DrawAxes(QPainter &painter, const QRect &plot_area) const
    {
        painter.setPen(QPen(Qt::black, 1.5));
        painter.drawRect(plot_area);

        painter.setPen(Qt::black);
        const float bin_width = (MaxX() - MinX()) / static_cast<float>(Bins);
        for (int bin = 0; bin < Bins; ++bin)
        {
            const float center = MinX()
                    + (static_cast<float>(bin) + 0.5f) * bin_width;
            const int x = static_cast<int>(ToPixelX(plot_area, center));
            const QRect tick_rect(x - 40, plot_area.bottom() + 4, 80, 18);
            painter.drawText(tick_rect, Qt::AlignHCenter | Qt::AlignTop,
                             QString::fromStdString(histogram->Canvas.Bins[bin]));
        }

        const QRect x_label_rect(plot_area.left(), rect().bottom() - 24,
                                 plot_area.width(), 20);
        painter.drawText(x_label_rect, Qt::AlignHCenter | Qt::AlignBottom,
                         QString::fromStdString(histogram->Canvas.XLabel));
        painter.save();
        painter.translate(18, plot_area.center().y());
        painter.rotate(-90);
        painter.drawText(-50, -10, 100, 20, Qt::AlignHCenter | Qt::AlignVCenter,
                         QString::fromStdString(histogram->Canvas.YLabel));
        painter.restore();
    }

    void DrawHistograms(QPainter &painter, const QRect &plot_area) const
    {
        const Histogram::DataFrame dataset = histogram->Get(parameter);
        const int count = static_cast<int>(dataset.size());
        if (dataset.empty()) return;
        const float baseline_y = ToPixelY(plot_area, histogram->Canvas.MinY);
        const float countFloat = static_cast<float>(count);

        for (int index = 0; index < count; ++index)
        {
            const Histogram::Data* data = dataset[index];
            if (data == nullptr) continue;
            const QColor color = ParseColor(data->Color);
            const float bin_count = static_cast<float>(Bins);
            const float bin_width = (MaxX() - MinX()) / bin_count;
            const float group_width = bin_width * 0.9f;
            const float bar_width = group_width / countFloat;
            const float group_offset = (static_cast<float>(index)
                    - (countFloat - 1.0f) / 2.0f) * bar_width;
            painter.setPen(QPen(color.darker(120), 1.0));
            painter.setBrush(color);

            Histogram::counts counts = data->Count(Bins);
            for (int bin = 0; bin < Bins; ++bin)
            {
                const float center = MinX()
                        + (static_cast<float>(bin) + 0.5f) * bin_width;
                const float count = counts[bin];
                const float left = ToPixelX(plot_area,
                        center + group_offset - bar_width / 2.0f);
                const float right = ToPixelX(plot_area,
                        center + group_offset + bar_width / 2.0f);
                const float top = ToPixelY(plot_area, count);

                const QRectF bar(std::min(left, right),
                        std::min(top, baseline_y), std::abs(right - left),
                        std::abs(baseline_y - top));
                painter.drawRect(bar);
            }
        }
    }

    void DrawLegend(QPainter &painter, const QRect &plot_area) const
    {
        set<pair<string, string>> labels;
        vector<LegendItem> items;
        for (const auto& bar: histogram->Get(parameter))
        {
            pair<string, string> p = make_pair(bar->Label, bar->Color);
            if (labels.count(p) > 0)
                continue;

            labels.emplace(p);
            items.push_back({bar->Label, ParseColor(bar->Color), LegendSwatch::Bar});
        }

        ::DrawLegend(painter, plot_area, items);
    }

    const Plot *histogram;
    float parameter = 0.0f;
    const int Bins;
};

class HistogramWindow final : public QWidget
{
public:
    explicit HistogramWindow(const Plot *plot) : histogram(plot)
    {
        setWindowTitle(QString::fromStdString(histogram->WindowTitle));
        resize(900, 700);

        auto *layout = new QVBoxLayout(this);

        title_label = new QLabel(this);
        layout->addWidget(title_label);

        histogram_canvas = new HistogramCanvas(histogram, this);
        layout->addWidget(histogram_canvas, 1);

        slider = new QSlider(Qt::Horizontal, this);
        slider->setRange(0, kSliderSteps);
        slider->setValue(0);
        layout->addWidget(slider);

        slider->setVisible(histogram->Slider);
        if (histogram->Slider)
        {
            connect(slider, &QSlider::valueChanged, this, [this](int value)
            {    UpdateDisplay(
                        SliderToParameter(value, histogram->MinP,
                                histogram->MaxP));
            });
        }

        UpdateDisplay(histogram->MinP);
    }

private:
    void UpdateDisplay(float parameter)
    {
        SetTitleLabel(*title_label,
                histogram->Slider ?
                        histogram->Title(parameter) : histogram->WindowTitle);
        histogram_canvas->SetParameter(parameter);
    }

    const Plot *histogram;
    QLabel *title_label = nullptr;
    HistogramCanvas *histogram_canvas = nullptr;
    QSlider *slider = nullptr;
};

class HistogramViewWindow final : public QWidget
{
public:
    HistogramViewWindow(const Plot *histogram, float parameter) : histogram(
            histogram)
    {
        setWindowTitle(QString::fromStdString(histogram->WindowTitle));
        resize(900, 700);

        auto *layout = new QVBoxLayout(this);

        title_label = new QLabel(this);
        SetTitleLabel(*title_label,
                histogram->Slider ?
                        histogram->Title(parameter) : histogram->WindowTitle);
        layout->addWidget(title_label);

        canvas = new HistogramCanvas(histogram, this);
        layout->addWidget(canvas, 1);
        canvas->SetParameter(parameter);
    }

private:
    const Plot *histogram;
    QLabel *title_label = nullptr;
    HistogramCanvas *canvas = nullptr;
};



void Plot::Show() const
    { RunQT(std::make_unique<HistogramWindow>(this)); }

void Plot::Show(const float parameter) const
    { RunQT(std::make_unique <HistogramViewWindow>(this, parameter)); }


class DynamicPlot final: public Plot
{
private:
    const Histogram::DynamicData& data;

public:
    DynamicPlot(const Histogram::Canvas& canvas, Histogram::DynamicData& ptr):
        Plot(canvas, ptr.MinP, ptr.MaxP), data(ptr) { }

    [[nodiscard]] string Title(float parameter) const override
        { return data.Title(parameter); }

    [[nodiscard]] Histogram::DataFrame Get(float parameter) const override
        { return const_cast<Histogram::DynamicData&>(data).Eval(parameter); }
};

void Histogram::Plot(const Histogram::Canvas& canvas, DynamicData& data)
{
    DynamicPlot plot(canvas, data);
    plot.Show();
}


class StaticPlot final: public Plot
{
private:
    const vector<Histogram::Data>& data;
    mutable vector<Histogram::Data*> result;

public:
    StaticPlot(const Histogram::Canvas& canvas, const vector<Histogram::Data>& d):
        Plot(canvas, 0.0, 0.0), data(d) { }

    [[nodiscard]] string Title(float parameter) const override
        { return ""; }

    [[nodiscard]] Histogram::DataFrame Get(float) const override
    {
        result.clear();
        for (const Histogram::Data& d : data)
            result.push_back(const_cast<Histogram::Data*>(&d));
        return result;
    }
};

void Histogram::Plot(const Histogram::Canvas& canvas, const vector<Histogram::Data>& data)
{
    StaticPlot plot(canvas, data);
    plot.Show();
}
