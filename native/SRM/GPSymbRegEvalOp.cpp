#include "GPSymbRegEvalOp.h"
#include "ReadData.h"
#include <vector>
//#include <boost/math/special_functions/fpclassify.hpp> // isnan, isinf

#include "MeanSquareErrorMetric.h"
#include "MeanAbsoluteErrorMetric.h"
#include "MeanAbsolutePercentageErrorMetric.h"

#include "IATree.h"
#include "IATerminal.h"
#include "infixTree.h"

// from WriteBest.h
extern bool evaluateVerbose;


void writeToXML(std::string& prefixTree, uint size, XMLNode& xTree)
{
	xTree = XMLNode::createXMLTopNode("Tree");
	xTree.addAttribute("size", uint2str(size).c_str());
	xTree.addText(prefixTree.c_str());
}


void GPSymbRegEvalOp::registerParameters(StateP state)
{
	state->getRegistry()->registerEntry("input_file", (voidP)(new std::string), ECF::STRING);
	state->getRegistry()->registerEntry("linear_scaling", (voidP) (new std::string), ECF::STRING);
	state->getRegistry()->registerEntry("error_weights.file", (voidP) (new std::string), ECF::STRING);
	state->getRegistry()->registerEntry("error_metric", (voidP) (new std::string), ECF::STRING);
	state->getRegistry()->registerEntry("bestfile", voidP(), ECF::STRING, "file to store best ind after each generation");
}


// called only once, before the evolution – generates training data
bool GPSymbRegEvalOp::initialize(StateP state)
{
	state_ = state;
	std::stringstream ss;
    voidP sptr = state->getRegistry()->getEntry("linear_scaling");
    ss << *((std::string*) sptr.get());
    std::string ls = ss.str();
    if (ls.compare("true") == 0) {
    	linearScaling = true;
    } else {
    	linearScaling = false;
    }
    ss.clear();

	// detect genotype
	GenotypeP activeGenotype = state->getGenotypes()[0];
	if (activeGenotype->getName() == "APGenotype")
		genotype = AP;
	else if (activeGenotype->getName() == "Tree")
		genotype = GP;
	else if (activeGenotype->getName() == "GEPChromosome")
		genotype = GEP;
	else {
		std::cout << "Unknown genotype in parameters!" << std::endl;
		return false;
	}


	x.clear();
	y.clear();
	f.clear();
	printDataPoints = false;
	
	// check if datafile is stated (used) in the conf. file
	if (state->getRegistry()->isModified("input_file")) {
		std::string dataFile = *((std::string*) state->getRegistry()->getEntry("input_file").get());

		// read from file into Evaluator data
		if (!eval.readDataFromFile(data, dataFile)) {
			std::cout << "Input file data reading error!" << std::endl;
			return false;
		}

		nSamples = data.size();
		nVariables = data[0].size() - 1;
		results.resize(nSamples);

		varNames.clear();

		for(uint i = 0; i < nVariables; i++) {
			varNames.push_back ("x" + uint2str(i + 1));
		}

		GenotypeP genotype = state->getGenotypes()[0];
		Tree::IATreeP iaTree = std::dynamic_pointer_cast<Tree::IATree>(genotype);
		
		if (iaTree) {
			for(uint i = 0; i < nVariables; i++) {
				IATerminalP terminal = std::dynamic_pointer_cast<IATerminal>(iaTree->primitiveSet_->getTerminalByName("x" + uint2str(i + 1)));
				//assert(terminal != 0);
				if (!terminal) {
					std::cout << "IATree init error!" << std::endl;
					return false;
				}
				double low = data[0][i];
				double up = low;
				for (uint j = 1; j < nSamples; j++) {
					double d = data[j][i];
					if (d > up) {
						up = d;
					}
					if (d < low) {
						low = d;
					}
				}

				terminal->lowerBound = low;
				terminal->upperBound = up;
			}
		}
	}

	// initialize the Evaluator
	eval.data = &data;
	eval.initialize();
	for (uint i = 0; i < nVariables; i++) {
		eval.addTerminal(varNames[i]);
	}

	errorWeightsDefined = false;

	if (state->getRegistry()->isModified("error_weights.file")) {
		std::string dataFile = *((std::string*) state->getRegistry()->getEntry("error_weights.file").get());

		std::vector< std::vector<double> > error_weights;

		// read from file into Evaluator data
		if (!readDataFromFile(error_weights, dataFile)) {
			return false;
		}

		errorWeightsDefined = true;

		unsigned int size = error_weights.size();
		for (uint i = 0; i < size; i++) {
			errorWeights.push_back(error_weights[i][0]);
		}

		if (size < nSamples) {
			std::cout << "Error weights count less than samples count." << std::endl;
			errorWeightsDefined = false;
			return false;
		}
	}

	if (state->getRegistry()->isModified("error_metric")) {
		std::string errorMetricStr = *((std::string*) state->getRegistry()->getEntry("error_metric").get());

		if (errorMetricStr.compare("mean_square_error") == 0) {
			errorMetric = new MeanSquareErrorMetric;
		} else if (errorMetricStr.compare("mean_absolute_error") == 0) {
			errorMetric = new MeanAbsoluteErrorMetric;
		} else if (errorMetricStr.compare("mean_absolute_percentage_error") == 0) {
			errorMetric = new MeanAbsolutePercentageErrorMetric;
		} else {
			std::cout << "Error metric unknown." << std::endl;
			return false;
		}
	} else {
		// default error metric
		errorMetric = new MeanSquareErrorMetric;
	}

	// best solution output file name
	bestFileName = "";
	if (state->getRegistry()->isModified("bestfile")) {
		sptr = state->getRegistry()->getEntry("bestfile");
		bestFileName = *((std::string*)sptr.get());
		ofstream bestFile(bestFileName);
		bestFile.close();
	}

	return true;
}


bool GPSymbRegEvalOp::csvRead(StateP state, std::string entry, std::vector<double>* vec)
{
	std::ifstream stream;
	std::string line;
	voidP sptr = state->getRegistry()->getEntry(entry);
	std::string fname = *((std::string*) sptr.get());
	stream.open(fname.c_str());
	if (!stream.is_open()) return false;
	while (getline(stream, line)){
		vec->push_back(atof(line.c_str()));
	}
	return true;
}


FitnessP GPSymbRegEvalOp::evaluateUsingLinearScaling(IndividualP individual, TreeP tree)
{
	// we try to minimize the function value, so we use FitnessMin fitness (for minimization problems)
	FitnessP fitness(new FitnessMin);

	//average value of y and t
	double mean_y = 0, mean_t = 0, sum_yt = 0, sum_sqr_y = 0;

	for (uint i = 0 ; i < nSamples ; i++)
	{
		double y;

		// a) usual Tree evaluation
		//// set only defined variables (x1, x2, ...)
		//for(uint term = 0; term < nVariables; term++) {
		//	if (tree->primitiveSet_->getTerminalByName(varNames[term]))
		//		tree->setTerminalValue(varNames[term], &data[i][term]);
		//}
		//// get the y value of the current tree
		//tree->execute(&y);

		// b) Evaluator:
		y = eval.executeParsedExpression(i);

		mean_y += y;
		double t = data[i][nVariables];
		mean_t += t;
		sum_yt += t*y;
		sum_sqr_y += y*y;
	}

	mean_y /= nSamples;
	mean_t /= nSamples;

	//coefficients for linear regression
	double b = (sum_yt - nSamples*mean_y*mean_t)/(sum_sqr_y - nSamples*mean_y*mean_y);
	double a = mean_t - b*mean_y;

	bool isNaN = std::isnan(a) || std::isnan(b);
	bool isInf = std::isinf(a) || std::isinf(b);
	if (isNaN || isInf) {	// set to neutral
		a = 0;
		b = 1;
	}

	double value = 0;
	double var_of_y = 0; //variance of variable result

	for(uint i = 0; i < nSamples; i++) {
		double y;

		// a) usual Tree evaluation
		//// set only defined variables (x1, x2, ...)
		//for(uint term = 0; term < nVariables; term++) {
		//	if (tree->primitiveSet_->getTerminalByName(varNames[term]))
		//		tree->setTerminalValue(varNames[term], &data[i][term]);
		//	dataWriter->writeData(data[i][term]);
		//	dataWriter->writeData('\t');
		//}
		//tree->execute(&y);

		// b) Evaluator:
		y = eval.executeParsedExpression(i);

		var_of_y += (y-mean_y)*(y-mean_y);
		// add the difference
		double t = data[i][nVariables];
		double result = a + b*y;
		dataWriter->writeData(result);
		dataWriter->writeData('\n');

		double error = errorMetric->calculateError(result, t);

		if (errorWeightsDefined) {
			error *= errorWeights[i];
		}

		value += error;
	}

	value /= nSamples;
	var_of_y /= nSamples-1;

	//delete expresion (but not explicit, just set fitness to big number)
	// if ( fabs(var_of_y) > 1e7 || fabs(var_of_y) < 1e-7 ) {
	// 	value = 1e14;
	// }

	if (printDataPoints || evaluateVerbose) {
		stringstream ss;
		string infix;
		showTree(infix, tree.get());
		// add linear scaling parameters to output
		ss << a << " + ";
		ss << b << " * ";
		ss << infix << endl;
		ECF_LOG(state_, 1, ss.str());

		// build Tree with linear scaling components
		IndividualP lsInd(individual->copy());
		TreeP lsTree(tree->copy());
		// output expression to prefix
		std::stringstream prefixTree;
		prefixTree << "+ D_" << a << " * D_" << b << " ";
		for (uint i = 0; i < tree->size(); i++) {
			prefixTree << (*tree)[i]->primitive_->getName() << " ";
		}
		// write prefix to XML
		XMLNode xTree = XMLNode::createXMLTopNode("Tree");
		xTree.addAttribute("size", uint2str(tree->size() + 4).c_str());
		xTree.addText(prefixTree.str().c_str());
		// read Tree from XML
		lsTree->read(xTree);
		// set in lsInd
		lsInd->resize(1);
		lsInd->at(0) = lsTree;

		std::ofstream bestFile(bestFileName, std::ios::app);
		bestFile << state_->getGenerationNo() << std::endl;
		bestFile << ss.str();
		bestFile << lsInd->toString() << std::endl;
		bestFile.close();
	}

	fitness->setValue(value);

	return fitness;
}


FitnessP GPSymbRegEvalOp::evaluateWithoutLinearScaling(IndividualP individual, TreeP tree)
{
	// we try to minimize the function value, so we use FitnessMin fitness (for minimization problems)
	FitnessP fitness(new FitnessMin);

	double value = 0;
	double result;

	// evaluating data from input file
	for (uint i = 0; i < nSamples; i++) {

		// a) usual Tree evaluation
		// set only defined variables (x1, x2, ...)
		//for(uint term = 0; term < nVariables; term++) {
		//	if(tree->primitiveSet_->getTerminalByName(varNames[term]))
		//		tree->setTerminalValue(varNames[term], &data[i][term]);
		//	dataWriter->writeData(data[i][term]);
		//	dataWriter->writeData('\t');
		//}
		// get the f value of the current tree
		//tree->execute(&result);

		// b) Evaluator:
		result = eval.executeParsedExpression(i);

		if (printDataPoints)
			results[i] = result;

		dataWriter->writeData(result);
		dataWriter->writeData('\n');

		// add error
		//value += fabs(data[i][nVariables] - result);
		double error = errorMetric->calculateError(result, data[i][nVariables]);
		
		if (errorWeightsDefined) {
			error *= errorWeights[i];
		}

		value += error;
	}

	//value /= pow(1.*nSamples, 2);	// divide with square
	value /= nSamples;
	fitness->setValue(value);

	if (printDataPoints || evaluateVerbose) {
		stringstream ss;
		string infix;
		showTree(infix, tree.get());
		ss << infix << endl;
		ECF_LOG(state_, 1, ss.str());

		// output to best solutions file
		IndividualP ind(individual->copy());
		ind->resize(1);
		ind->at(0) = tree;

		std::ofstream bestFile(bestFileName, std::ios::app);
		bestFile << state_->getGenerationNo() << std::endl;
		bestFile << ss.str();
		bestFile << ind->toString() << std::endl;
		if (printDataPoints)
			for (auto& data : results)
				bestFile << data << std::endl;
		bestFile.close();
	}

	return fitness;
}


FitnessP GPSymbRegEvalOp::evaluate(IndividualP individual)
{
	TreeP tree;

	// get the genotype defined in the configuration file, convert to Tree
	if(genotype == GP)
		//Tree::Tree* tree = (Tree::Tree*)individual->getGenotype().get();
		// (you can also use boost smart pointers:)
		tree = std::static_pointer_cast<Tree::Tree> (individual->getGenotype());
	else if (genotype == AP) {
		// AP genotype hack: if evaluateVerbose, use the tree stored in individual
		if(evaluateVerbose)
			tree = std::static_pointer_cast<Tree::Tree> (individual->getGenotype(1));
		else {
			// if AP genotype is used, convert to Tree
			TreeP APtree = (TreeP)((Tree::APGenotype*)individual->getGenotype().get())->convertToPhenotype();
			// copy nodes
			tree = std::static_pointer_cast<Tree::Tree> (individual->getGenotype(1));
			tree->clear();
			for (uint i = 0; i < APtree->size(); i++)
				tree->addNode(APtree->at(i));
			tree->update();
		}
	}
	else if (genotype == GEP) {
		GEPChromosomeP gep = std::static_pointer_cast<GEP::GEPChromosome> (individual->getGenotype());

		uint nTrees = (uint)(gep->genes) + 1;
		uint exprSize = 0;

		// Transform genes into subtrees and store them in a vector
		std::vector<TreeP> trees;
		trees.push_back((TreeP)gep->makeCellTree());
		for (uint g = 0; g < nTrees - 1; g++) {
			trees.push_back((TreeP)gep->toTree(g));
		}

		// output tree expressions to strings
		std::vector< std::string > genes(nTrees);
		for (uint t = 0; t < nTrees; t++) {
			for (uint i = 0; i < trees[t]->size(); i++) {
				genes[t] += (*trees[t])[i]->primitive_->getName() + " ";
			}
		}

		// build single prefix expression
		std::string expression, token;
		std::stringstream ss(genes[0]);
		while (ss >> token) {
			if (token.compare(0, 4, "GENE") == 0) {
				uint geneId = 1 + str2uint(token.substr(5));
				expression += genes[geneId];
				exprSize += trees[geneId]->size();
			}
			else {
				expression += token + " ";
				exprSize++;
			}
		}

		// build Tree
		tree = (TreeP)new Tree::Tree();
		XMLNode xTree = XMLNode::createXMLTopNode("Tree");
		xTree.addAttribute("size", uint2str(exprSize).c_str());
		xTree.addText(expression.c_str());
		tree->primitiveSet_ = gep->primitiveSet_;
		tree->read(xTree);
	}

	// use the Evaluator to parse GP tree
	readIndividual(tree);

	if (linearScaling) {
		return evaluateUsingLinearScaling(individual, tree);
	} else {
		return evaluateWithoutLinearScaling(individual, tree);
	}
}


// read an individual into Evaluator parsedExpression - Tree version
void GPSymbRegEvalOp::readIndividual(TreeP tree)
{
	// output tree expression to string
	std::stringstream sValue;
	for (uint i = 0; i < tree->size(); i++) {
		sValue << (*tree)[i]->primitive_->getName() << " ";
	}
	// send expression to evaluator
	eval.parseExpression(sValue.str(), tree->size());

	return;
}


