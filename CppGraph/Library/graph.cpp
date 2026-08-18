#include "graph.h"
#include "common.h"

#include <memory>
#include <set>
#include <utility>
#include <vector>
#include <QLabel>
#include <QSlider>
#include <QVBoxLayout>
#include <QWidget>
#include <QPaintEvent>
#include <QPainter>
#include <QPainterPath>
#include <QPalette>
#include <QPen>
#include <QColor>
#include <QPointF>
#include <QRect>

using namespace std;


Graph::DynamicData::~DynamicData() = default;


class Plot
{
public:
    const string WindowTitle;
    const Graph::Canvas Canvas;
    const float MinP;
    const float MaxP;
    const bool Slider;

    Plot(const Graph::Canvas& canvas, const float minP, const float maxP):
        WindowTitle(canvas.Title), Canvas(canvas), Slider(minP != maxP),
        MinP(minP), MaxP(maxP) { }

    void Show() const;
    void Show(float) const;

    [[nodiscard]] virtual string Title(float parameter) const = 0;
    [[nodiscard]] virtual Graph::DataFrame Get(float) const = 0;
    virtual ~Plot() = default;
};


class GraphCanvas final : public QWidget
{
public:
    explicit GraphCanvas(const Plot *g, QWidget *parent = nullptr):
        QWidget(parent), graph(g)
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

        for (const Graph::Data* data : graph->Get(parameter))
            if (data != nullptr) DrawCurve(painter, plot_area, data);
        DrawLegend(painter, plot_area);
    }

private:
    [[nodiscard]] QRect PlotArea() const
    {
        return rect().adjusted(kPlotMarginLeft, kPlotMarginTop,
                -kPlotMarginRight, -kPlotMarginBottom);
    }

    [[nodiscard]] QPointF ToPixel(const QRect &plot_area, float x, float y) const
    {
        const float x_range = graph->Canvas.MaxX - graph->Canvas.MinX;
        const float y_range = graph->Canvas.MaxY - graph->Canvas.MinY;

        const float x_ratio =
                x_range == 0.0f ? 0.0f : (x - graph->Canvas.MinX) / x_range;
        const float y_ratio =
                y_range == 0.0f ? 0.0f : (y - graph->Canvas.MinY) / y_range;

        return QPointF(plot_area.left() + x_ratio * plot_area.width(),
                plot_area.bottom() - y_ratio * plot_area.height());
    }

    void DrawBackground(QPainter &painter) const
    {
        painter.fillRect(rect(), QColor(252, 252, 252));
        painter.fillRect(PlotArea(), Qt::white);
    }

    static void DrawGrid(QPainter &painter, const QRect &plot_area)
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
        const QRect x_label_rect(plot_area.left(), rect().bottom() - 24,
                                 plot_area.width(), 20);
        painter.drawText(x_label_rect, Qt::AlignHCenter | Qt::AlignBottom,
                         QString::fromStdString(graph->Canvas.XLabel));
        painter.save();
        painter.translate(18, plot_area.center().y());
        painter.rotate(-90);
        painter.drawText(-50, -10, 100, 20, Qt::AlignHCenter | Qt::AlignVCenter,
                         QString::fromStdString(graph->Canvas.YLabel));
        painter.restore();
    }

    void DrawCurve(QPainter &painter, const QRect &plot_area,
                   const Graph::Data* data) const
    {
        const QColor color = ParseColor(data->Color);

        const auto points = data->Points;
        if (points.empty()) return;

        if (data->Bullet)
        {
            QPen pen(color, 1.5);
            painter.setPen(pen);
            painter.setBrush(color);

            constexpr double kPointRadius = 1.25;
            for (auto point : points)
            {
                const QPointF p = ToPixel(plot_area, point.first, point.second);
                painter.drawEllipse(p, kPointRadius, kPointRadius);
            }
            return;
        }

        QPen pen(color, 2.0);
        pen.setCapStyle(Qt::RoundCap);
        pen.setJoinStyle(Qt::RoundJoin);
        painter.setPen(pen);
        painter.setBrush(Qt::NoBrush);

        QPainterPath path;
        bool started = false;
        for (auto it : points)
        {
            const QPointF point = ToPixel(plot_area, it.first, it.second);
            if (!started)
            {
                path.moveTo(point);
                started = true;
            }
            else
                path.lineTo(point);
        }
        painter.drawPath(path);
    }

    void DrawLegend(QPainter &painter, const QRect &plot_area) const
    {
        set<pair<string, string>> labels;
        vector<LegendItem> items;
        for (const auto& curve : graph->Get(parameter))
        {
            pair<string, string> p = make_pair(curve->Label, curve->Color);
            if (labels.count(p) > 0)
                continue;

            labels.emplace(p);
            items.push_back(
                { curve->Label, ParseColor(curve->Color),
                    curve->Bullet ? LegendSwatch::Point : LegendSwatch::Line });
        }

        ::DrawLegend(painter, plot_area, items);
    }

    const Plot *graph;
    float parameter = 0.0f;
};


class GraphWindow final : public QWidget
{
public:
    explicit GraphWindow(const Plot *g) : graph(g)
    {
        setWindowTitle(QString::fromStdString(graph->WindowTitle));
        resize(900, 700);

        auto *layout = new QVBoxLayout(this);

        title_label = new QLabel(this);
        layout->addWidget(title_label);

        plot_canvas = new GraphCanvas(graph, this);
        layout->addWidget(plot_canvas, 1);

        slider_ = new QSlider(Qt::Horizontal, this);
        slider_->setRange(0, kSliderSteps);
        slider_->setValue(0);
        layout->addWidget(slider_);

        slider_->setVisible(graph->Slider);
        if (graph->Slider)
            connect(slider_, &QSlider::valueChanged, this, [this](int value)
            { UpdateDisplay(
                SliderToParameter(value, graph->MinP, graph->MaxP)); });


        UpdateDisplay(graph->MinP);
    }

private:
    void UpdateDisplay(float parameter) const {
        SetTitleLabel(*title_label,
                graph->Slider ?
                        graph->Title(parameter) : graph->WindowTitle);
        plot_canvas->SetParameter(parameter);
    }

    const Plot *graph;
    QLabel *title_label = nullptr;
    GraphCanvas *plot_canvas = nullptr;
    QSlider *slider_ = nullptr;
};


class GraphViewWindow final : public QWidget
{
public:
    GraphViewWindow(const Plot *g, float parameter) : graph(g)
    {
        setWindowTitle(QString::fromStdString(graph->WindowTitle));
        resize(900, 700);

        auto *layout = new QVBoxLayout(this);

        title_label = new QLabel(this);
        SetTitleLabel(*title_label,
                graph->Slider ?
                        graph->Title(parameter) : graph->WindowTitle);
        layout->addWidget(title_label);

        canvas = new GraphCanvas(graph, this);
        layout->addWidget(canvas, 1);
        canvas->SetParameter(parameter);
    }

private:
    const Plot *graph;
    QLabel *title_label = nullptr;
    GraphCanvas *canvas = nullptr;
};


void Plot::Show() const
    { RunQT(std::make_unique<GraphWindow>(this)); }

void Plot::Show(const float parameter) const
    { RunQT(std::make_unique <GraphViewWindow>(this, parameter)); }


class DynamicPlot final: public Plot
{
private:
    const Graph::DynamicData& data;

public:
    DynamicPlot(const Graph::Canvas& canvas, Graph::DynamicData& ptr):
        Plot(canvas, ptr.MinP, ptr.MaxP), data(ptr) { }

    [[nodiscard]] string Title(float parameter) const override
        { return data.Title(parameter); }

    [[nodiscard]] Graph::DataFrame Get(float parameter) const override
        { return const_cast<Graph::DynamicData&>(data).Eval(parameter); }
};

void Graph::Plot(const Graph::Canvas& canvas, DynamicData& data)
{
    DynamicPlot plot(canvas, data);
    plot.Show();
}


class StaticPlot final: public Plot
{
private:
    const vector<Graph::Data>& data;
    mutable vector<Graph::Data*> result;

public:
    StaticPlot(const Graph::Canvas& canvas, const vector<Graph::Data>& d):
        Plot(canvas, 0.0, 0.0), data(d) { }

    [[nodiscard]] string Title(float parameter) const override
        { return ""; }

    [[nodiscard]] Graph::DataFrame Get(float) const override
    {
        result.clear();
        for (const Graph::Data& d : data)
            result.push_back(const_cast<Graph::Data*>(&d));
        return result;
    }
};

void Graph::Plot(const Graph::Canvas& canvas, const vector<Graph::Data>& data)
{
    StaticPlot plot(canvas, data);
    plot.Show();
}
