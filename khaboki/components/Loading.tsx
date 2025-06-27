import { Loader2, UtensilsCrossed } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="text-center py-12">
        <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
        <h3 className="mt-4 text-lg font-semibold">
          Finding the best restaurants...
        </h3>
        <p className="text-gray-600 mt-2">This may take a few moments</p>

        {/* Loading skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden">
              <div className="h-48 bg-gray-200 animate-pulse"></div>
              <CardContent className="p-4 space-y-3">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3 animate-pulse"></div>
                <div className="flex justify-between">
                  <div className="h-3 bg-gray-200 rounded w-16 animate-pulse"></div>
                  <div className="h-3 bg-gray-200 rounded w-16 animate-pulse"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="text-center py-16">
      <UtensilsCrossed className="h-16 w-16 mx-auto text-gray-400 mb-4" />
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        No restaurants found
      </h3>
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        We couldn&apos;t find any restaurants in this area. Try adjusting your
        location or search filters.
      </p>
    </div>
  );
}