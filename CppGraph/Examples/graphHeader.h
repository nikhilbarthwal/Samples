#include <cmath>
#include <graph.h>

using namespace std;


const float N = static_cast<float>(500);
const float Pi = 3.141593f;
const float factor = 2.0f * Pi / N;


class CurveData final : public Graph::Data
{
public:
    CurveData(const string& color, const string& label, const Graph::points& pts,
              bool bullet) : Graph::Data(color, label, pts, bullet) {}
};


inline CurveData SinCurve(float frequency)
{
    Graph::points pts;
    for (int i = 0; i < N; ++i)
    {
        const float x = static_cast<float>(i);
        pts[x] = sin(frequency * factor * x);
    }
    return CurveData("blue", "Sin(x)", pts, false);
}


inline CurveData CosCurve(float frequency)
{
    Graph::points pts;
    for (int i = 0; i < N; ++i)
    {
        const float x = static_cast<float>(i);
        pts[x] = cos(frequency * factor * x);
    }
    return CurveData("red", "Cos(x)", pts, true);
}
