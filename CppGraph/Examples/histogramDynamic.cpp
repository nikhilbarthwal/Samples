#include <cmath>
#include <histogram.h>
#include <memory>
#include <string>
#include <vector>

using namespace std;


const vector<string> Bins = {
    "Bin0", "Bin1", "Bin2", "Bin3", "Bin4", "Bin5",
    "Bin6", "Bin7", "Bin8", "Bin9" };

const int BinCount = static_cast<int>(Bins.size());

class GaussianData
{
private:
    unique_ptr<Histogram::Data> data;
    vector<float> values;
    string color;
    string label;
    float mean;
    float sigma;

public:
    GaussianData(string color, string label, float mean, float sigma):
        color(std::move(color)), label(std::move(label)), mean(mean),
        sigma(sigma)
    {
        values.resize(BinCount);
    }

    Histogram::Data* Eval(float p)
    {
        for (int bin = 0; bin < BinCount; ++bin)
        {
            const float x = static_cast<float>(bin) + 0.5f;
            const float exponent = -((x - mean) * (x - mean))
                    / (2.0f * sigma * sigma);
            values[bin] = p * 10.0f * std::exp(exponent);
        }
        data = make_unique<Histogram::Data>(color, label, values);
        return data.get();
    }
};


class GaussianDynamicData final : public Histogram::DynamicData
{
private:
    GaussianData g1;
    GaussianData g2;
    GaussianData g3;
    vector<Histogram::Data*> result = { nullptr, nullptr, nullptr };

public:
    GaussianDynamicData() :
        Histogram::DynamicData(0.5f, 2.0f),
        g1("blue", "Blue", 4.0f, 1.2f),
        g2("green", "Green", 7.0f, 1.5f),
        g3("red", "Red", 2.5f, 0.9f) { }

    [[nodiscard]] string Title(float parameter) const override
    {
        return "Gaussian Mixture (p = " + to_string(parameter) + ")";
    }

    [[nodiscard]] Histogram::DataFrame Eval(float p) override
    {
        result[0] = g1.Eval(p);
        result[1] = g2.Eval(p);
        result[2] = g3.Eval(p);
        return result;
    }
};


int main()
{
    const Histogram::Canvas canvas("Dynamic Histogram", "Bin", "Count", Bins,
                                   0.0f, 12.0f);
    GaussianDynamicData data;
    Histogram::Plot(canvas, data);
    return 0;
}
