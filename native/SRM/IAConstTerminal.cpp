#include "GPSymbRegEvalOp.h"

#include "IATree.h"
#include "IAConstTerminal.h"
#include <cmath>

void IAConstTerminal::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}

	Tree::Primitives::Terminal::execute(result, tree);
}

IABounds IAConstTerminal::calculateBounds(Tree::IATree& tree) {
	IABounds retVal;
	double val;
	this->getValue(&val);

	retVal.isWithinBounds = true;
	retVal.isLowerBoundInclusive = true;
	retVal.lowerBound = val;
	retVal.isUpperBoundInclusive = true;
	retVal.upperBound = val;
	return retVal;
}
