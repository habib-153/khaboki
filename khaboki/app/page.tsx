/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useState, useEffect } from "react";
import { MapPin, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RestaurantCache } from "@/lib/RestaurantCache";
import { EmptyState, LoadingState } from "@/components/Loading";
import { RestaurantGrid } from "@/components/RestaurantGrid";
import { ScrapeResults, SearchFiltersType } from "@/types";
import { LocationModal } from "@/components/LocationModal";
import logo from "@/public/1000083585.png"
import { useSurpriseRestaurant } from "@/hooks/useSurpriseRestaurant";
import { SurpriseModal } from "@/components/SurpriseModal";
import Image from "next/image";

export default function Home() {
  const [searchValue, setSearchValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [restaurants, setRestaurants] = useState<ScrapeResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFiltersType>({
    cuisineType: "",
    minRating: 0,
    maxDeliveryTime: 60,
    platforms: ["foodpanda", "foodi"],
    maxDeliveryFee: 100,
    sortBy: "rating",
  });

  // Search and filter states
  const [cuisineSearch, setCuisineSearch] = useState<string>("");
  const [sortBy, setSortBy] = useState<"rating" | "delivery_time" | "offers">(
    "rating"
  );

  // Location modal state
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locationDisplayText, setLocationDisplayText] =
    useState("Select location");

  const {
    getSurpriseRestaurant,
    surpriseRestaurant,
    isLoading: surpriseLoading,
    setSurpriseRestaurant,
    previousSuggestions,
    resetSuggestions,
  } = useSurpriseRestaurant();

  const [showSurpriseModal, setShowSurpriseModal] = useState(false);

  const [cacheInfo, setCacheInfo] = useState<{
    hasCache: boolean;
    age?: number;
    location?: string;
  }>({ hasCache: false });

  // Load Google Maps script
  useEffect(() => {
    const loadGoogleMapsScript = () => {
      if (document.querySelector('script[src*="maps.googleapis.com"]')) {
        return; // Script already loaded
      }

      const googleMapScript = document.createElement("script");
      googleMapScript.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places`;
      googleMapScript.async = true;
      googleMapScript.defer = true;
      window.document.body.appendChild(googleMapScript);
    };

    if (!window.google) {
      loadGoogleMapsScript();
    }
  }, []);

  useEffect(() => {
    const cached = RestaurantCache.load();
    if (cached) {
      setRestaurants(cached.restaurants as ScrapeResults);
      setSelectedLocation(cached.location);
      setSearchValue(cached.searchText);
      setLocationDisplayText(cached.searchText || "Location selected");
      setCacheInfo(RestaurantCache.getCacheInfo());
    }
  }, []);

  const fetchRestaurants = async (forceRefresh = false) => {
    const currentLocation = selectedLocation;
    const currentSearchText = searchValue
console.log(currentSearchText)
    if (!currentLocation) {
      setError("Please select a location first");
      return;
    }

    if (!forceRefresh) {
      const cachedData = RestaurantCache.shouldUseCache(
        currentLocation,
        currentSearchText
      );
      if (cachedData) {
        setRestaurants(cachedData.restaurants);
        setCacheInfo(RestaurantCache.getCacheInfo());
        console.log("Using cached data");
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lat: currentLocation.lat,
          lng: currentLocation.lng,
          text: currentSearchText,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setRestaurants(data.results);

        RestaurantCache.save({
          restaurants: data.results,
          location: currentLocation,
          searchText: currentSearchText,
          filters,
        });

        setCacheInfo(RestaurantCache.getCacheInfo());
      } else {
        setError(data.error || "Failed to fetch restaurants");
      }
    } catch (err) {
      setError(
        "Failed to connect to server. Please check your internet connection."
      );
      console.error("Error fetching data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocationSelect = (
    location: { lat: number; lng: number },
    address: string
  ) => {
    setSelectedLocation(location);
    setSearchValue(address);
    setLocationDisplayText(address.split(",")[0] || address); 
    // setTimeout(() => fetchRestaurants(), 100);
  };

  const handleConfirmLocationAndSearch = (
    location: { lat: number; lng: number },
    address: string
  ) => {
    setSelectedLocation(location);
    // setSearchValue(address.split(",")[0] || address);
    setSearchValue(address);
    setLocationDisplayText(address);
    console.log("🎯 handleConfirmLocationAndSearch called with:", {
      location,
      address,
    });
    setTimeout(() => fetchRestaurants(), 100);
  };

  const clearCache = () => {
    RestaurantCache.clear();
    setCacheInfo({ hasCache: false });
    setRestaurants(null);
  };

  const hasResults =
    restaurants && (restaurants.foodpanda?.length || restaurants.foodi?.length);

  const handleSurpriseMe = async () => {
    if (!restaurants) {
      setError("Please search for restaurants first");
      return;
    }

    setShowSurpriseModal(true);
    await getSurpriseRestaurant(restaurants, filters, false);
  };

  const handleRefreshSurprise = async () => {
    if (restaurants) {
      await getSurpriseRestaurant(restaurants, filters, true);
    }
  };

  const handleCloseSurpriseModal = () => {
    setShowSurpriseModal(false);
  };

  return (
    <div className="min-h-screen bg-surface-50">
      {/* Modern Header */}
      <header className="bg-brand-primary backdrop-blur-lg border-b border-surface-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <Image src={logo} alt="logo" height={50} width={200} />
            {/* <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-brand-primary to-brand-secondary rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">K</span>
              </div>
              <div>
                <h1 className="text-2xl text-white font-bold">Khabo ki?</h1>
                <p className="text-white text-sm">Find your perfect meal</p>
              </div>
            </div> */}

            {/* Location Search */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowLocationModal(true)}
                  className="bg-white border-white/20 text-brand-primary hover:text-primary hover:bg-white backdrop-blur-sm min-w-[200px] justify-start"
                >
                  <MapPin size={16} className="mr-2" />
                  <span className="truncate">
                    {locationDisplayText.length > 20
                      ? `${locationDisplayText.substring(0, 20)}...`
                      : locationDisplayText}
                  </span>
                </Button>

                {hasResults && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fetchRestaurants(true)}
                    disabled={isLoading}
                    className="bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm"
                  >
                    {isLoading ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <RefreshCw size={16} />
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Error message */}
        {error && (
          <Alert
            variant="destructive"
            className="border-brand-danger/20 bg-brand-danger/5"
          >
            <AlertDescription className="text-brand-danger">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {isLoading && <LoadingState />}

        {!isLoading && hasResults && (
          <div className="space-y-6">
            {/* Controls Section */}
            <Card className="border-0 shadow-sm bg-white/70 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                  {/* Left side - Search and Sort */}
                  <div className="flex flex-col sm:flex-row gap-4 flex-1">
                    {/* Cuisine Search */}
                    <div className="flex-1 max-w-sm">
                      <Input
                        placeholder="Search by cuisine or restaurant name..."
                        value={cuisineSearch}
                        onChange={(e) => setCuisineSearch(e.target.value)}
                        className="h-10 border-surface-300 focus:border-brand-primary focus:ring-brand-primary/20"
                      />
                    </div>

                    {/* Sort Options */}
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-surface-600 whitespace-nowrap">
                        Sort by:
                      </span>
                      <div className="flex gap-1">
                        <Button
                          variant={sortBy === "rating" ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSortBy("rating")}
                          className={
                            sortBy === "rating"
                              ? "bg-brand-primary hover:bg-brand-primary/90"
                              : "border-surface-300 text-surface-600 hover:bg-surface-100"
                          }
                        >
                          Rating
                        </Button>
                        <Button
                          variant={
                            sortBy === "delivery_time" ? "default" : "outline"
                          }
                          size="sm"
                          onClick={() => setSortBy("delivery_time")}
                          className={
                            sortBy === "delivery_time"
                              ? "bg-brand-primary hover:bg-brand-primary/90"
                              : "border-surface-300 text-surface-600 hover:bg-surface-100"
                          }
                        >
                          Delivery Time
                        </Button>
                        <Button
                          variant={sortBy === "offers" ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSortBy("offers")}
                          className={
                            sortBy === "offers"
                              ? "bg-brand-primary hover:bg-brand-primary/90"
                              : "border-surface-300 text-surface-600 hover:bg-surface-100"
                          }
                        >
                          Offers
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Right side - Surprise Me Button */}
                  <Button
                    onClick={handleSurpriseMe}
                    disabled={surpriseLoading}
                    className="bg-brand-primary shadow-lg"
                  >
                    <Sparkles size={16} className="mr-2" />
                    Surprise Me!
                  </Button>
                </div>
              </CardContent>
            </Card>

            <RestaurantGrid
              restaurants={restaurants!}
              filters={{ ...filters, sortBy }}
              cuisineSearch={cuisineSearch}
            />
          </div>
        )}

        {!isLoading && !hasResults && !selectedLocation && (
          <div className="text-center py-12">
            <MapPin size={48} className="mx-auto text-surface-400 mb-4" />
            <h3 className="text-lg font-medium text-surface-900 mb-2">
              Select Your Location
            </h3>
            <p className="text-surface-600 mb-6">
              Click on the location button in the header to get started
            </p>
          </div>
        )}

        {!isLoading && !hasResults && restaurants && <EmptyState />}
      </main>

      {/* Location Modal */}
      <LocationModal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        onLocationSelect={handleConfirmLocationAndSearch} 
        initialLocation={selectedLocation}
        initialAddress={searchValue}
        isLoading={isLoading}
      />

      <SurpriseModal
        isOpen={showSurpriseModal}
        onClose={handleCloseSurpriseModal}
        restaurant={surpriseRestaurant}
        onRefresh={handleRefreshSurprise}
        isLoading={surpriseLoading}
        previousCount={previousSuggestions.length}
      />
    </div>
  );
}

declare global {
  interface Window {
    google: typeof google;
    initMap?: () => void;
  }
}