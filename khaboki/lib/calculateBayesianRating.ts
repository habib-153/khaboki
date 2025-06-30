export function calculateBayesianRating(rating: string, platform: string) {
  // Parse rating and count
  const match = rating.match(/(\d+\.?\d*)\((\d+)\+?\)/);
  if (!match) return { rating: 0, adjustedRating: 0, confidence: "low" };

  const avgRating = parseFloat(match[1]);
  const reviewCount = parseInt(match[2].replace(/\+$/, ""));

  // Platform-specific priors (based on your dataset analysis)
  const priors = {
    foodpanda: { avgPrior: 4.2, minReviews: 100 },
    foodi: { avgPrior: 3.8, minReviews: 50 },
    all: { avgPrior: 4.0, minReviews: 75 },
  };

  const prior = priors[platform as keyof typeof priors] || priors.all;

  // Bayesian adjustment formula
  const adjustedRating =
    (prior.avgPrior * prior.minReviews + avgRating * reviewCount) /
    (prior.minReviews + reviewCount);

  // Confidence based on review count
  const confidence =
    reviewCount >= 100 ? "high" : reviewCount >= 25 ? "medium" : "low";

  return {
    rating: avgRating,
    adjustedRating: Math.round(adjustedRating * 10) / 10,
    reviewCount,
    confidence,
  };
}