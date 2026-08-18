#include <graph.h>
#include "graphHeader.h"


int main()
{
    const Graph::Canvas canvas("Static Graph Example", "Frequency", "Magnitute",
                               0.0f, N, -1.0f, 1.0f);
    const vector<Graph::Data> data = { SinCurve(1.0f), CosCurve(1.0f) };
    Graph::Plot(canvas, data);
    return 0;
}
