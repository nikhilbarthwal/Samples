#include <iostream>

#include <string>
#include <stdexcept>
#include <climits>
#include <cctype>
#include <cstdlib>

using namespace std;

// Trim string of all leading & trailing white spaces!
string Trim(const string &str) {
    int i = 0, j = 0;
    while (isspace(str[i]))
        i++;

    while (!isspace(str[i + j]))
        if ((i + j) == str.length() - 1)
            return str.substr(i);
        else
            j++;

    return str.substr(i, j);
}

int Convert(const string &str) {
    string s = Trim(str);
    const int n = s.length();

    if (n == 0)
        throw runtime_error("Empty string");

    bool sign = true;       // Assume the number is positive;
    int p = 0;              // Starting position for the string is beginning
    const char c = s[0];    // get the first character of the string

    if (c == '-') {
        p++;
        sign = false; // Number is negative
    } else {
        if (c == '+')
            p++;
    }

    for (int i = p; i < n; i++)
        if ((s[i] < '0') || (s[i] > '9'))
            throw runtime_error("Invalid format");

    while (s[p] == '0') // Optimization: Trim all leading zeroes
        p++;

    const int limit = sign ? INT_MAX : INT_MIN;
    int result = 0;
    int exp = (sign) ? 1 : -1;
    for (int i = n - 1; i >= p; i--) {
        int delta = exp * (s[i] - '0');

        // Check if there is more room to add, then add else throw overflow exception
        if ((sign) ? ((limit - result) >= delta) : ((limit - result) <= delta))
            result += delta;
        else
            throw overflow_error("Integer overflow");


        // If the limit of # of digits have reached and there are still more digits left
        // to be processed, then throw overflow exception.
        if ((((double) limit / exp) < (double) 10) && (i > p))
            throw overflow_error("Integer overflow");
        else
            exp *= 10;
    }

    return result;
}

void test(string str)
{
    cout<<"\""<<str<<"\"\t-->\t";
    try
    {
        cout<<Convert(str)<<endl;
    }
    catch(const exception& e)
    {
        cout<<"EXCEPTION - "<<e.what()<<endl;
    }

}


int main(void) {
    test("+000002147483647");
    test("-0000002147483648");
    test("    02147483648  ");
    test(" adfasfdgher ewr");
    return 0;
}

