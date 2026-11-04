#include "GPSymbRegEvalOp.h"

#include "IATree.h"
#include <ecf/tree/Tree.h>
#include "IAConstTerminal.h"
#include "IAERCD.h"

//using namespace Tree;
namespace Tree {

IATree::IATree() {
	name_ = "IATree";
	boundsCalculated = false;
	startDepth_ = 0;
}

IATree* IATree::copy() {
	IATree *newObject = new IATree(*this);
	return newObject;
}

void IATree::initializeFirst(Tree* hometree) {

	// create and link PrimitiveSet to the hometree
	hometree->primitiveSet_ = (PrimitiveSetP) (new PrimitiveSet);
	hometree->primitiveSet_->initialize(state_);
	this->primitiveSet_ = hometree->primitiveSet_;

	// add user defined functions to primitiveSet
	for(int i = 0; i < (int) userFunctions_.size(); i++) {
		primitiveSet_->mAllPrimitives_[userFunctions_[i]->getName()] = userFunctions_[i];
		primitiveSet_->mAllPrimitives_[userFunctions_[i]->getName()]->initialize(state_);
	}

	// read function set from the configuration
	voidP sptr = getParameterValue(state_, "functionset");
	std::stringstream names;
	std::string name;
	names << *((std::string*) sptr.get());
	while(names >> name) {
		if(!primitiveSet_->addFunction(name)) {
			ECF_LOG_ERROR(state_, "Error: unknown function in function set (\'" + name + "\')!");
			throw("");
		}
	}
	if(primitiveSet_->getFunctionSetSize() == 0) {
		ECF_LOG_ERROR(state_, "Tree genotype: empty function set!");
		throw("");
	}

	// set default terminal type
	Primitives::terminal_type currentType = Primitives::Double;
	type_iter typeIter;

	// read terminal set from the configuration
	std::stringstream tNames;
	sptr = getParameterValue(state_, "terminalset");
	tNames << *((std::string*) sptr.get());

	while(tNames >> name)
	{
		// read current terminal type (if set)
		typeIter = primitiveSet_->mTypeNames_.find(name);
		if(typeIter != primitiveSet_->mTypeNames_.end()) {
			currentType = typeIter->second;
			continue;
		}

		// see if it's a user-defined terminal 
		uint iTerminal = 0;
		for(; iTerminal < userTerminals_.size(); iTerminal++)
			if(userTerminals_[iTerminal]->getName() == name)
				break;
		if(iTerminal < userTerminals_.size()) {
			userTerminals_[iTerminal]->initialize(state_);
			primitiveSet_->addTerminal(userTerminals_[iTerminal]);
			continue;
		}


		// read ERC definition (if set)
		// ERC's are defined as interval [x y] or set {a b c}
		if(name[0] == '[' || name[0] == '{') {

			std::string ercValues = "";

			// name this ERC (ERC's name is its value!)
			PrimitiveP erc = (PrimitiveP) (new IAERCD);
			ercValues = DBL_PREFIX;

			while(name[name.size() - 1] != ']' && name[name.size() - 1] != '}') {
				ercValues += " " + name;
				tNames >> name;
			}
			ercValues += " " + name;

			// ERC ocekuje "D_ [<value> <value> ...]" kao ime prije initialize()
			erc->setName(ercValues);
			erc->initialize(state_);
			primitiveSet_->addTerminal(erc);

			continue;
		} 


		// otherwise, read terminal of current type
		PrimitiveP terminal = (PrimitiveP) (new IAConstTerminal);

		// if the 'name' can be identified as a value of the 'currentType', then it's a _constant terminal_ (of that value)
		// otherwise, it's a regular terminal with 'name'
		std::istringstream ss(name);
		switch(currentType)
		{
			case Primitives::Double:
				double dblValue;
				ss >> dblValue;
				if(ss.fail() == false) 
					terminal->setValue(&dblValue);
				break;
			case Primitives::Int:
				int intValue;
				ss >> intValue;
				if(ss.fail() == false) 
					terminal->setValue(&intValue);
				break;
			case Primitives::Bool:
				bool boolValue;
				ss >> boolValue;
				if(name == "true")
					boolValue = true;
				else if(name == "false")
					boolValue = false;
				if(ss.fail() == false || name == "true" || name == "false") {
					if(boolValue)
						name = "true";
					else
						name = "false";
					terminal->setValue(&boolValue);
				}
				break;
			case Primitives::Char:
				char charValue;
				ss >> charValue;
				if(ss.fail() == false) 
					terminal->setValue(&charValue);
				break;
			case Primitives::String:
				std::string stringValue;
				ss >> stringValue;
				if(ss.fail() == false) 
					terminal->setValue(&stringValue);
				break;
		}
		terminal->setName(name);
		primitiveSet_->addTerminal(terminal);
		
	}

	if(primitiveSet_->getTerminalSetSize() == 0) {
		ECF_LOG_ERROR(state_, "Tree: Empty terminal set!");
		throw("");
	}

	// read tree depth constraints, store in hometree
	sptr = getParameterValue(state_, "maxdepth");
	hometree->maxDepth_ = *((uint*) sptr.get());
	sptr = getParameterValue(state_, "mindepth");
	hometree->minDepth_ = *((uint*) sptr.get());
	if(hometree->maxDepth_ < hometree->minDepth_ || hometree->maxDepth_ < 1) {
		ECF_LOG_ERROR(state_, "Tree genotype: invalid values for max and min tree depth!");
		throw("");
	}

	hometree->initMaxDepth_ = hometree->maxDepth_;
	if(isParameterDefined(state_, "initmaxdepth")) {
		sptr = getParameterValue(state_, "initmaxdepth");
		hometree->initMaxDepth_ = *((uint*) sptr.get());
	}
	hometree->initMinDepth_ = hometree->minDepth_;
	if(isParameterDefined(state_, "initmindepth")) {
		sptr = getParameterValue(state_, "initmindepth");
		hometree->initMinDepth_ = *((uint*) sptr.get());
	}
	if(hometree->initMaxDepth_ < hometree->initMinDepth_ || hometree->initMaxDepth_ < 1) {
		ECF_LOG_ERROR(state_, "Tree genotype: invalid values for initial max and min tree depth!");
		throw("");
	}
	if(hometree->initMaxDepth_ > hometree->maxDepth_) {
		ECF_LOG_ERROR(state_, "Tree genotype: initial max depth cannot be greater than evolution max depth!");
		throw("");
	}
}

}