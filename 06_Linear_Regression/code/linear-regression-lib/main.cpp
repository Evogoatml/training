#include <iostream>
#include <string>
#include "linreg.h"

using namespace std;

int main()
{
    LinearRegresion Test;
    Test.getDataPaths("dependent_vars.txt", "independent_vars.txt");
    Test.Regression();
}
