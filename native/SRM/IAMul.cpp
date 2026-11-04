#include "GPSymbRegEvalOp.h"

#include "IAMul.h"
#include "IATree.h"
#include <cmath>

void IAMul::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}
	
	Tree::Primitives::Mul::execute(result, tree);
}

IABounds IAMul::calculateBounds(Tree::IATree& tree) {
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
		double ll = bounds1.lowerBound * bounds2.lowerBound;
		double lu = bounds1.lowerBound * bounds2.upperBound;
		double ul = bounds1.upperBound * bounds2.lowerBound;
		double uu = bounds1.upperBound * bounds2.upperBound;

		IABounds retVal;
		if (ll <= lu && ll <= ul && ll <= uu) {
			// ll is min
			retVal.isLowerBoundInclusive = bounds1.isLowerBoundInclusive && bounds2.isLowerBoundInclusive;
			retVal.lowerBound = ll;	
		} else if (lu <= ll && lu <= ul && lu <= uu) {
			// lu is min
			retVal.isLowerBoundInclusive = bounds1.isLowerBoundInclusive && bounds2.isUpperBoundInclusive;
			retVal.lowerBound = lu;
		} else if (ul <= ll && ul <= lu && ul <= uu) {
			// ul is min
			retVal.isLowerBoundInclusive = bounds1.isUpperBoundInclusive && bounds2.isLowerBoundInclusive;
			retVal.lowerBound = ul;
		} else {
			// uu is min
			retVal.isLowerBoundInclusive = bounds1.isUpperBoundInclusive && bounds2.isUpperBoundInclusive;
			retVal.lowerBound = uu;
		}

		if (ll >= lu && ll >= ul && ll >= uu) {
			// ll is max
			retVal.isUpperBoundInclusive = bounds1.isLowerBoundInclusive && bounds2.isLowerBoundInclusive;
			retVal.upperBound = ll;
		} else if (lu >= ll && lu >= ul && lu >= uu) {
			// lu is max
			retVal.isUpperBoundInclusive = bounds1.isLowerBoundInclusive && bounds2.isUpperBoundInclusive;
			retVal.upperBound = lu;
		} else if (ul >= ll && ul >= lu && ul >= uu) {
			// ul is max
			retVal.isUpperBoundInclusive = bounds1.isUpperBoundInclusive && bounds2.isLowerBoundInclusive;
			retVal.upperBound = ul;
		} else {
			// uu is max
			retVal.isUpperBoundInclusive = bounds1.isUpperBoundInclusive && bounds2.isUpperBoundInclusive;
			retVal.upperBound = uu;
		}

		retVal.isWithinBounds = true;
		return retVal;
	}
}
