#ifndef GPSymbRegEvalOp_h
#define GPSymbRegEvalOp_h


/**
* \defgroup symbreg Symbolic regression (GP)
* \ingroup examples
* \brief Symbolic regression example - illustration for Tree genotype (see more on this example in help/tutorial.html)
*
* \par Description
* The objective is to find a symbolic form of an unknown function (i.e. find a mapping between the given set
* of input and output values).
* The fitness is defined with total error for the given set of output values.
*
* \par Tree genotype parameters (in the config file)
* - set of functions (inner tree nodes)
* - set of terminals (variables and constants, tree leaves)
* - min and max tree depth
*
*/


/**
* \ingroup symbreg
* \brief Symbolic regression evaluation operator.
*/
#include <cmath>
#include <ecf/ECF.h>
#include <fstream>
#include "Evaluator.h"
#include "DataWriter.h"
#include "ErrorMetric.h"

class GPSymbRegEvalOp : public EvaluateOp
{
public:
	FitnessP evaluate(IndividualP individual);
	bool initialize(StateP);
	void registerParameters(StateP);
	bool csvRead(StateP state, std::string entry, std::vector<double>* vec);
	void readIndividual(TreeP tree);

	std::vector< std::vector<double> > data;
	Evaluator eval;

	std::vector<double> x;
	std::vector<double> y;
	std::vector<double> f;
	uint nSamples;
	uint nVariables;
	std::vector<string> varNames;
	bool linearScaling;

	bool printDataPoints;
	std::vector<double> results;
	DataWriter* dataWriter;
	bool errorWeightsDefined;
	std::vector<double> errorWeights;
	std::string bestFileName;
	enum Genotype{ GP, AP, GEP };
	Genotype genotype;

	ErrorMetric* errorMetric;

private:
	FitnessP evaluateUsingLinearScaling(IndividualP individual, TreeP tree);
	FitnessP evaluateWithoutLinearScaling(IndividualP individual, TreeP tree);
	StateP state_;

};
typedef std::shared_ptr<GPSymbRegEvalOp> GPSymbRegEvalOpP;

#endif // GPSymbRegEvalOp_h
