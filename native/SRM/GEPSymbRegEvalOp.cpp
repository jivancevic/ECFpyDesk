#include "GEPSymbRegEvalOp.h"
#include "ReadData.h"


//
// ispis Tree u infix formatu
//
uint GEPSymbRegEvalOp::showTree(string& output, Tree::Tree* tree, uint iNode, uint prefix)
{
	Tree::PrimitiveP prim = tree->at(iNode)->primitive_;
	int arity = prim->getNumberOfArguments();

	if (arity == 0) {
		if (prim->getName().rfind("D_", 0) == 0)
			output += prim->getName().substr(2);
		else
			output += prim->getName();
	}
	else if (prim->getName() == "P2") {
		output += "P2(";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ", ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ")";
	}
	else if (prim->getName() == "ADD" ||
		prim->getName() == "AND" ||
		prim->getName() == "NAND" ||
		prim->getName() == "AND2" ||
		prim->getName() == "XOR" ||
		prim->getName() == "XNOR" ||
		prim->getName() == "NOR" ||
		prim->getName() == "OR") {
		output += "(";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += " " + prim->getName() + " ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ")";
	}
	else if (prim->getName() == "MUL") {
		output += "(";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += " * ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ")";
	}
	else if (prim->getName() == "NOT") {
		output += "~";
		output += "(";
		for (int child = 0; child < arity; child++) {
			iNode++;
			iNode = showTree(output, tree, iNode, prefix);
		}
		output += ")";
	}
	else if (prim->getName() == "IF") {
		output += "IF(";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ", ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ", ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ")";
	}
	else if (arity == 2) {
		output += "(";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += " " + prim->getName() + " ";
		iNode++;
		iNode = showTree(output, tree, iNode, prefix);
		output += ")";
	}
	else if (arity == 1) {
		output += prim->getName();
		output += "(";
		for (int child = 0; child < arity; child++) {
			iNode++;
			iNode = showTree(output, tree, iNode, prefix);
		}
		output += ")";
	}
	return iNode;
}


void GEPSymbRegEvalOp::registerParameters(StateP state)
{
	state->getRegistry()->registerEntry("input_file", (voidP)(new std::string), ECF::STRING);
}


// called only once, before the evolution – generates training data
bool GEPSymbRegEvalOp::initialize(StateP state)
{
	x.clear();
	y.clear();
	f.clear();

	// check if the parameters are stated (used) in the conf. file
	if (state->getRegistry()->isModified("input_file")) {
		std::string dataFile = *((std::string*) state->getRegistry()->getEntry("input_file").get());

		// read from file into Evaluator data
		if (!eval.readDataFromFile(data, dataFile)) {
			std::cout << "Input file data reading error!" << std::endl;
			return false;
		}

		nSamples = data.size();
		nVariables = data[0].size() - 1;

		varNames.clear();

		for (uint i = 0; i < nVariables; i++) {
			varNames.push_back("x" + uint2str(i + 1));
		}

		// initialize the Evaluator
		eval.data = &data;
		eval.initialize();
		for (uint i = 0; i < nVariables; i++) {
			eval.addTerminal(varNames[i]);
		}

		return true;
	}


	nSamples = 10;
	double s = 1;
	double X = -10*s;
	double Y = -10*s;

	for (uint i = 0; i < nSamples; i++) {
		x.push_back(X);
		y.push_back(Y);
		Y += 2*s;
		X += 2*s;
	}

	for (uint i = 0; i < nSamples; i++) {
		X = x.at(i);
		for (uint j = 0; j < nSamples; j++) {
			Y = y.at(j);
			// F1
			f.push_back(sin(X) + sin(Y*Y)); // F2
			//f.push_back(2*sin(X)*cos(Y)); // F3
			//f.push_back(X*Y + sin((X + 1)*(Y - 1))); // F4
			//f.push_back(8 / (2+X*X+Y*Y)); // F5
			//f.push_back((X*X*X)/5+(Y*Y*Y)/2-X-Y); // F6
		}
	}
	return true;

}


bool GEPSymbRegEvalOp::csvRead(StateP state, std::string entry, std::vector<double>* vec){
	std::ifstream stream;
	std::string line;
	voidP sptr = state->getRegistry()->getEntry(entry);
	std::string fname = *((std::string*) sptr.get());
	stream.open(fname);
	if (!stream.is_open()) return false;
	while (getline(stream, line)){
		vec->push_back(atof(line.c_str()));
	}
	return true;
}


FitnessP GEPSymbRegEvalOp::evaluate(IndividualP individual)
{
	// we try to minimize the function value, so we use FitnessMin fitness (for minimization problems)
	FitnessP fitness(new FitnessMin);
	// get genotype
	GEPChromosomeP gep = std::static_pointer_cast<GEP::GEPChromosome> (individual->getGenotype());
	// The system is multigenic. We iterate over every gene, transform it to a tree, execute it and link it with the results of its fellow genes

	readIndividual(individual);
	double value = 0;
	double result;
	//nSamples = f.size();
	for(uint i = 0; i < nSamples; i++) {
		result = eval.executeParsedExpression(i);

		// add the difference
		value += pow(data[i][nVariables] - result, 2);
		// += fabs(f.at(i*nSamples + j) - result);
	}
	value /= pow(1.*nSamples, 2);
	fitness->setValue(value);
	return fitness;
}


// read an individual into Evaluator parsedExpression - GEP version
void GEPSymbRegEvalOp::readIndividual(IndividualP individual)
{
	GEPChromosomeP gep = std::static_pointer_cast<GEP::GEPChromosome> (individual->getGenotype());
	//std::cout << gep->toString();

	uint nTrees = (uint)(gep->genes) + 1;
	uint exprSize = 0;

	// Transform genes into subtrees and store them in a vector
	std::vector<TreeP> trees;
	trees.push_back((TreeP) gep->makeCellTree());
	for (uint g = 0; g < nTrees - 1; g++) {
		trees.push_back((TreeP) gep->toTree(g));
	}

	// output tree expressions to strings
	std::vector< std::string > genes(nTrees);
	for (uint t = 0; t < nTrees; t++) {
		for (uint i = 0; i < trees[t]->size(); i++) {
			genes[t] += (*trees[t])[i]->primitive_->getName() + " ";
		}
		//std::cout << genes[t] << std::endl;
	}

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
	std::cout << expression << std::endl;

	// send expression to evaluator
	eval.parseExpression(expression, exprSize);

	XMLNode xTree = XMLNode::createXMLTopNode("Tree");
	xTree.addAttribute("size", uint2str(exprSize).c_str());
	xTree.addText(expression.c_str());
	trees[0]->primitiveSet_ = gep->primitiveSet_;
	trees[0]->read(xTree);
	showTree(expression, trees[0].get());
	std::cout << expression << std::endl;
}
