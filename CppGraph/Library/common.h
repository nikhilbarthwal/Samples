#pragma once

#include <QApplication>
#include <QColor>
#include <QLabel>
#include <QPainter>
#include <QWidget>
#include <memory>
#include <string>
#include <vector>

class QPainter;
class QPaintEvent;

constexpr int kSliderSteps = 1000;
constexpr int kPlotMarginLeft = 60;
constexpr int kPlotMarginRight = 20;
constexpr int kPlotMarginTop = 20;
constexpr int kPlotMarginBottom = 50;

using namespace std;


float SliderToParameter(int slider_value, float min_p, float max_p);

QColor ParseColor(const string &color);

void SetTitleLabel(QLabel &label, const string &title);


enum class LegendSwatch
{
    Line,
    Point,
    Bar,
};


struct LegendItem
{
    string label;
    QColor color;
    LegendSwatch swatch = LegendSwatch::Line;
};


void DrawLegend(QPainter &painter, const QRect &plot_area,
                const std::vector<LegendItem> &items);

vector<float> GraphLinspace(float min_x, float max_x, size_t count);


#define RunQT(function) { \
    const bool owns_application = QApplication::instance() == nullptr; \
    std::unique_ptr<QApplication> owned_application; \
    int argc = 0; \
    if (owns_application) \
        owned_application = std::make_unique<QApplication>(argc, nullptr); \
    std::unique_ptr<QWidget> window = function ;  \
    window->show(); \
    if (owns_application) QApplication::exec(); }
