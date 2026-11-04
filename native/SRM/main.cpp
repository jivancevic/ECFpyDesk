#include <ecf/ECF.h>
#include "GEPSymbRegEvalOp.h"
#include "GPSymbRegEvalOp.h"
#include "FileDataWriter.h"
#include "WriteBest.h"

#include "Sqrt.h"
#include "Log.h"
#include "Avg.h"

#include "IATree.h"
#include "IAAdd.h"
#include "IASub.h"
#include "IAMul.h"
#include "IADiv.h"
#include "IASin.h"
#include "IACos.h"
#include "IASqrt.h"
#include "IALog.h"
#include "IATerminal.h"



namespace Tree {
namespace Primitives {

/**
 * \ingroup tree genotypes primitives
 * \brief Arccos function primitive (Tree genotype)
 */
class ACos : public Primitive
{
public:
	ACos(void);
	void execute(void* result, Tree& tree);
	~ACos(void);
};

ACos::ACos(void)
{
	nArguments_ = 1;
	name_ = "acos";
}

ACos::~ACos(void)
{	}

#define _USE_MATH_DEFINES
#include<math.h>
void ACos::execute(void* result, Tree &tree)
{
	double& arg = *(double*)result;
    getNextArgument(&arg, tree);
	if (arg >= -1 && arg <= 1) {
		arg = acos(arg);
	} else if (arg > 1)
		arg = 0;
	else
		arg = M_PI;
}

}
}


class IAACos : public Tree::Primitives::ACos, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

void IAACos::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}
	
	ACos::execute(result, tree);
}

IABounds IAACos::calculateBounds(Tree::IATree& tree) {
	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds = prim->calculateBounds(tree);

	if (!bounds.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds;
	} else if (bounds.lowerBound < -1 || bounds.upperBound > 1) {
		IABounds retVal;
		retVal.isWithinBounds = false;
		return retVal;
	} else {
		// subtree is ok
		IABounds retVal;
		retVal.isWithinBounds = true;
		retVal.isLowerBoundInclusive = bounds.isLowerBoundInclusive;
		retVal.lowerBound = acos(bounds.lowerBound);
		retVal.isUpperBoundInclusive = bounds.isUpperBoundInclusive;
		retVal.upperBound = acos(bounds.upperBound);
		return retVal;
	}
}




namespace Tree {
namespace Primitives {

/**
 * \ingroup tree genotypes primitives
 * \brief Arcsin function primitive (Tree genotype)
 */
class ASin : public Primitive
{
public:
	ASin(void);
	void execute(void* result, Tree& tree);
	~ASin(void);
};

ASin::ASin(void)
{
	nArguments_ = 1;
	name_ = "asin";
}

ASin::~ASin(void)
{	}

#define _USE_MATH_DEFINES
#include<math.h>
void ASin::execute(void* result, Tree &tree)
{
	double& arg = *(double*)result;
    getNextArgument(&arg, tree);
	if (arg >= -1 && arg <= 1) {
		arg = asin(arg);
	} else if (arg > 1)
		arg = M_PI / 2;
	else
		arg = -M_PI / 2;
}

}
}


class IAASin : public Tree::Primitives::ASin, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

void IAASin::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}
	
	ASin::execute(result, tree);
}

IABounds IAASin::calculateBounds(Tree::IATree& tree) {
	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds = prim->calculateBounds(tree);

	if (!bounds.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds;
	} else if (bounds.lowerBound < -1 || bounds.upperBound > 1) {
		IABounds retVal;
		retVal.isWithinBounds = false;
		return retVal;
	} else {
		// subtree is ok
		IABounds retVal;
		retVal.isWithinBounds = true;
		retVal.isLowerBoundInclusive = bounds.isLowerBoundInclusive;
		retVal.lowerBound = asin(bounds.lowerBound);
		retVal.isUpperBoundInclusive = bounds.isUpperBoundInclusive;
		retVal.upperBound = asin(bounds.upperBound);
		return retVal;
	}
}



int main(int argc, char **argv)
{
    StateP state (new State);

    // set the evaluation operator

	GPSymbRegEvalOp *op = new GPSymbRegEvalOp;
	DataWriter dataWriter;
	op->dataWriter = &dataWriter;

	//GEPSymbRegEvalOp* op = new GEPSymbRegEvalOp;

    state->setEvalOp(op);

    TreeP tree = (TreeP) new Tree::Tree;
    Tree::Primitives::PrimitiveP sqrtPrimitive = (Tree::Primitives::PrimitiveP) new Tree::Primitives::Sqrt;
    tree->addFunction(sqrtPrimitive);
    Tree::Primitives::PrimitiveP logPrimitive = (Tree::Primitives::PrimitiveP) new Tree::Primitives::Log;
    tree->addFunction(logPrimitive);
    Tree::Primitives::PrimitiveP acosPrimitive = (Tree::Primitives::PrimitiveP) new Tree::Primitives::ACos;
    tree->addFunction(acosPrimitive);
    Tree::Primitives::PrimitiveP asinPrimitive = (Tree::Primitives::PrimitiveP) new Tree::Primitives::ASin;
    tree->addFunction(asinPrimitive);
	Tree::Primitives::PrimitiveP avgPrimitive = (Tree::Primitives::PrimitiveP) new Tree::Primitives::Avg;
	tree->addFunction(avgPrimitive);

	state->addGenotype(tree);

	APGenotypeP ap = (APGenotypeP) new Tree::APGenotype;
	ap->addFunction(sqrtPrimitive);
	ap->addFunction(logPrimitive);
	ap->addFunction(acosPrimitive);
	ap->addFunction(asinPrimitive);
	ap->addFunction(avgPrimitive);

	state->addGenotype(ap);

	GEPChromosomeP gep = (GEPChromosomeP) new GEP::GEPChromosome;
	gep->addFunction(avgPrimitive);
	gep->addFunction(sqrtPrimitive);
	gep->addFunction(logPrimitive);

	state->addGenotype(gep);



    Tree::IATreeP iaTree(new Tree::IATree);
    // create new functions and add them to function set
    Tree::PrimitiveP iaAdd(new IAAdd);
    iaTree->addFunction(iaAdd);
    Tree::PrimitiveP iaSub(new IASub);
    iaTree->addFunction(iaSub);
    Tree::PrimitiveP iaMul(new IAMul);
    iaTree->addFunction(iaMul);
    Tree::PrimitiveP iaDiv(new IADiv);
    iaTree->addFunction(iaDiv);
    Tree::PrimitiveP iaSin(new IASin);
    iaTree->addFunction(iaSin);
    Tree::PrimitiveP iaCos(new IACos);
    iaTree->addFunction(iaCos);
    Tree::PrimitiveP iaSqrt(new IASqrt);
    iaTree->addFunction(iaSqrt);
    Tree::PrimitiveP iaLog(new IALog);
    iaTree->addFunction(iaLog);
	Tree::PrimitiveP iaACos(new IAACos);
    iaTree->addFunction(iaACos);
    Tree::PrimitiveP iaASin(new IAASin);
    iaTree->addFunction(iaASin);

    // custom type terminals
    for(uint i = 0; i < 99; i++) {
        Tree::PrimitiveP myTerm = (Tree::PrimitiveP) new IATerminal;
        std::string name = "x" + uint2str(i);
        myTerm->setName(name);
        iaTree->addTerminal(myTerm);
    }

    state->addGenotype(iaTree);

    // add writeout of best individual each generation
    state->addOperator((OperatorP) new WriteBest);

    // initialize & run
    state->initialize(argc, argv);

    if (argc >= 3) {
        // read best solution from the file (argv[2]), evaluate it on test data and save to out file (argv[3])
        XMLNode xInd = XMLNode::parseFile(argv[2], "Individual");
        IndividualP ind = (IndividualP) new Individual(state);
        ind->read(xInd);

		// print linear scaling parameters
        //op->printParams = true;
        //std::string testOutFile(argv[3]);
        //FileDataWriter fileDataWriter(testOutFile);
        //op->dataWriter = &fileDataWriter;
		evaluateVerbose = true;
		op->printDataPoints = true;
		ind->fitness = state->getEvalOp()->evaluate(ind);
        //dataWriter.close();
        std::cout << ind->toString();
    } else {
        // run experiment
		state->run();

        // after the evolution: show best 
        //std::vector<IndividualP> hof = state->getHoF()->getBest();
        //IndividualP ind = hof[0];
        // std::cout << ind->toString();
        
        // print linear scaling parameters
        //op->printParams = true;
        //state->getEvalOp()->evaluate(ind);
    }
    
    return 0;
}
