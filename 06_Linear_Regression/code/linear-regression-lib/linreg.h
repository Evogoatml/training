#ifndef LINREG_H
#define LINREG_H
#include <string>
#include <vector>

class LinearRegresion
{
private:

    //VARIABLES

    //paths of data files
    std::string d_path;
    std::string i_path;

    std::vector<double> dependent_vars; //vector for dependent vars
    std::vector<double> independent_vars; //vector for independent vars

    std::vector<double> predicted_vars; //vector for predicted vars

    int observation_num; //number of "dots" on our graph
    double dep_mean; //mean value for dependent vars
    double ind_mean; //mean value for independent vars
    double b1; //slope in equation
    double b0; //intercept in equation
    double sse; //sum of square errors
    double sst;
    double ssr;
    double det_c;

    //METHODS

    void getObservationNum();

    void calculateDepMean();
    void calculateIndMean();

    void calculateB1();
    void calculateB0();

    void getPredictions(); // makes vector with predicted dep vals

    void calculateSST();
    void calculateSSE();
    void calculateSSR();

    void calculateDeterminationC();

public:

    //INIT PART
    void fillVectors();
    void getDataPaths(std::string path1, std::string path2);// gets paths for dependent/independent data

    //VARIOUS PRINTS
    void printCentroid();
    void printErrors();
    void printParameters();
    void printPredictions();
    void printCoef();

    //MAIN FUNCTION
    void Regression();

};



#endif // LINREG_H
