#include "GPSymbRegEvalOp.h"

#include "IATree.h"
#include "IATerminal.h"
#include <cmath>

void IATerminal::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}

	Tree::Primitives::Terminal::execute(result, tree);
}

IABounds IATerminal::calculateBounds(Tree::IATree& tree) {
	IABounds retVal;
	retVal.isWithinBounds = true;
	retVal.isLowerBoundInclusive = true;
	retVal.lowerBound = lowerBound;
	retVal.isUpperBoundInclusive = true;
	retVal.upperBound = upperBound;
	return retVal;
}
