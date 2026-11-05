#include "GPSymbRegEvalOp.h"

#include "IAAdd.h"
#include "IATree.h"
#include <cmath>

void IAAdd::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}
	
	Tree::Primitives::Add::execute(result, tree);
}

IABounds IAAdd::calculateBounds(Tree::IATree& tree) {
	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim1 = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds1 = prim1->calculateBounds(tree);

	if (!bounds1.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds1;
	}

	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim2 = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds2 = prim2->calculateBounds(tree);

	if (!bounds2.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds2;
	} else {
		// subtree is ok
		IABounds retVal;
		retVal.isWithinBounds = true;
		retVal.isLowerBoundInclusive = bounds1.isLowerBoundInclusive && bounds2.isLowerBoundInclusive;
		retVal.lowerBound = bounds1.lowerBound + bounds2.lowerBound;
		retVal.isUpperBoundInclusive = bounds1.isUpperBoundInclusive && bounds2.isUpperBoundInclusive;
		retVal.upperBound = bounds1.upperBound + bounds2.upperBound;
		return retVal;
	}
}
