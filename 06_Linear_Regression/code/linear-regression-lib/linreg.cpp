#include "linreg.h"
#include <iostream>
#include <string>
#include <fstream>

using namespace std;

//loading part
void LinearRegresion::getDataPaths(string path1, string path2)
{
    d_path = path1;
    i_path = path2;
}
void LinearRegresion::fillVectors()
{
    //Fill dependent_vars
    ifstream d_data(d_path);
    double d_num = 0.0;
    while(d_data >> d_num)
    {
        dependent_vars.push_back(d_num);
    }

    //Fill independent_vars
    ifstream i_data(i_path);
    double i_num = 0.0;
    while(i_data >> i_num)
    {
        independent_vars.push_back(i_num);
    }
}
void LinearRegresion::getObservationNum()
{
    observation_num = independent_vars.size();
}

//calculations of means
void LinearRegresion::calculateDepMean()
{
    dep_mean = 0;
    int s = 0;
    for(int i = 0; i < observation_num; i++)
    {
        dep_mean = dep_mean + dependent_vars.at(i);
        s++;
    }
    dep_mean = dep_mean / s;
}
void LinearRegresion::calculateIndMean()
{
    ind_mean = 0;
    int s = 0;
    for(int i = 0; i < observation_num; i++)
    {
        ind_mean = ind_mean + independent_vars.at(i);
        s++;
    }
    ind_mean = ind_mean / s;
}

//calculations of parameters
void LinearRegresion::calculateB1()
{
    double e1 = 0; //current ind var - ind_mean
    double e2 = 0; //current dep var - dep_mean
    double e3 = 0; //e1 squared

    double s1 = 0;// final sum will be s1/s2
    double s2 = 0;

    for(int i = 0; i < observation_num; i++)
    {
        e1 = independent_vars.at(i) - ind_mean;
        e2 = dependent_vars.at(i) - dep_mean;
        s1 += e1 * e2;

        e3 = e1 * e1;
        s2 += e3;
    }
    b1 = s1/s2;
}
void LinearRegresion::calculateB0()
{
    b0 = dep_mean - b1 * ind_mean;
}

//getting predicted values
void LinearRegresion::getPredictions()
{
    double s;
    for(int i = 0; i < observation_num; i++)
    {
        s = b1 * independent_vars.at(i) + b0;
        predicted_vars.push_back(s);
    }
}

//caluculating errors
void LinearRegresion::calculateSST()
{
    sst = 0;
    double s;
    for(int i = 0; i < observation_num; i++)
    {
        s = dependent_vars.at(i) -dep_mean;
        sst += s*s;
    }
}
void LinearRegresion::calculateSSE()
{
    sse = 0;
    double s;
    for(int i = 0; i < observation_num; i++)
    {
        s = dependent_vars.at(i) - predicted_vars.at(i);
        sse += s*s;
    }
}
void LinearRegresion::calculateSSR()
{
    ssr = sst - sse;
}
//calculating coefficient of determination
void LinearRegresion::calculateDeterminationC()
{
    det_c = ssr / sst;
}

//various prints
void LinearRegresion::printCentroid()
{
    cout << "CENTROID COORDINATES" << endl;
    cout << ind_mean << " " << dep_mean << endl;
    cout << endl;
}
void LinearRegresion::printPredictions()
{
    cout << "PREDICTED VALUES" << endl;
    for(int i = 0; i < observation_num; i++)
        cout << predicted_vars.at(i) << endl;
    cout << endl;
}
void LinearRegresion::printParameters()
{
    cout << "PARAMETERS" << endl;
    cout << "b1: " << b1 << " " << "b0: " << b0 << endl;
    cout << endl;
}
void LinearRegresion::printErrors()
{
    cout << "ERRORS" << endl;
    cout << "sst: " << sst << endl;
    cout << "sse: " << sse << endl;
    cout << "ssr: " << ssr << endl;
    cout << endl;
}
void LinearRegresion::printCoef()
{
    cout << "COEFFICIENT OF DETERMINATION" << endl;
    cout << "determination c is: " << det_c << " or " << det_c * 100 << "%" << endl;
    cout << endl;
}
void LinearRegresion::Regression() //calculates and prints everything
{
    fillVectors();
    getObservationNum();

    calculateIndMean();
    calculateDepMean();

    calculateB1();
    calculateB0();

    getPredictions();

    calculateSST();
    calculateSSE();
    calculateSSR();

    calculateDeterminationC();

    printCentroid();
    printPredictions();
    printParameters();
    printErrors();
    printCoef();
}
