#pragma once

#include <map>
#include <memory>
#include <string>
#include <vector>

#if defined(_WIN32) || defined(__CYGWIN__)
#  ifdef GRAPH_PLOT_BUILD_DLL
#    define GRAPH_API __declspec(dllexport)
#  else
#    define GRAPH_API
#  endif
#else
#  define GRAPH_API
#endif

using namespace std;


namespace Graph
{
    typedef map<float, float> points;

    class Data
    {
    public:
        const string Color;
        const string Label;
        const bool Bullet;
        const points Points;

        Data(const string& color, const string& label,
             const points& pts, const bool bullet):
            Color(color), Label(label), Points(pts), Bullet(bullet) { }
    };

    typedef vector<Data*>& DataFrame;

    struct Canvas
    {
        const string Title;
        const string XLabel;
        const string YLabel;
        const float MinX;
        const float MaxX;
        const float MinY;
        const float MaxY;
        Canvas(const Canvas&) = default;

        Canvas(const string& title, const string& xLabel, const string& yLabel,
               const float minX, const float maxX,
               const float minY, const float maxY):
            Title(title), XLabel(xLabel), YLabel(yLabel),
            MinX(minX), MaxX(maxX), MinY(minY), MaxY(maxY) { }
    };

    class DynamicData
    {
    public:
        const float MinP;
        const float MaxP;

        DynamicData(const float minP, const float maxP):
            MinP(minP), MaxP(maxP) { }
        virtual ~DynamicData();

        [[nodiscard]] virtual string Title(float parameter) const = 0;
        [[nodiscard]] virtual DataFrame Eval(float) = 0;
    };

    GRAPH_API void Plot(const Canvas&, const vector<Data>&);
    GRAPH_API void Plot(const Canvas&, DynamicData&);
};
