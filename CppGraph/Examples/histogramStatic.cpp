#include <cmath>
#include <histogram.h>
#include <memory>
#include <string>
#include <vector>


Histogram::Canvas canvas("Static Histogram", "", "Count",
        {"A", "B", "C", "D", "E"}, 0.0f, 10.0f);
Histogram::Data d1("blue", "Series A", {2.0f, 5.0f, 8.0f, 4.0f, 1.0f, 2.0f });
Histogram::Data d2("orange", "Series B", { 1.0f, 3.0f, 6.0f, 7.0f });

int main()
{
    Histogram::Plot(canvas, {d1, d2});
    return 0;
}
