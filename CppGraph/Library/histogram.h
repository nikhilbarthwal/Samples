#pragma once

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


namespace Histogram
{
    typedef vector<float> counts;

    class Data
    {
    private:
        const counts Values;

    public:
        const string Color;
        const string Label;

        Data(const string& color, const string& label, const counts& values):
            Color(color), Label(label), Values(values) { }

        counts Count(const int) const;
    };

    typedef vector<Data*>& DataFrame;

    struct Canvas
    {
        const string Title;
        const string XLabel;
        const string YLabel;
        const vector<string> Bins;
        const float MinY;
        const float MaxY;
        const int Size;

        Canvas(const Canvas&) = default;

        Canvas(const string& title, const string& xLabel, const string& yLabel,
               const vector<string>& bins, const float minY, const float maxY):
            Title(title), XLabel(xLabel), YLabel(yLabel), Bins(bins),
            MinY(minY), MaxY(maxY), Size(static_cast<int>(bins.size())) { }
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
