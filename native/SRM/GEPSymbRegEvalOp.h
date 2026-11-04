#ifndef SymbRegEvalOp_h
#define SymbRegEvalOp_h


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

class GEPSymbRegEvalOp : public EvaluateOp
{
public:
	uint showTree(string& output, Tree::Tree* tree, uint iNode = 0, uint prefix = 0);

	FitnessP evaluate(IndividualP individual);
	bool initialize(StateP);
	void registerParameters(StateP);
	bool csvRead(StateP state, std::string entry, std::vector<double>* vec);
	void readIndividual(IndividualP individual);

	std::vector<double> x;
	std::vector<double> y;
	std::vector<double> f;
	std::vector< std::vector<double> > data;
	uint nSamples;
	uint nVariables;
	std::vector<string> varNames;

	Evaluator eval;
};
typedef std::shared_ptr<GEPSymbRegEvalOp> GEPSymbRegEvalOpP;

#endif // SymbRegEvalOp_h
