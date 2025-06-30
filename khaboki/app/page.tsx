/* eslint-disable @typescript-eslint/no-unused-vars */

"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { MapPin, Search, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { RestaurantCache } from "@/lib/RestaurantCache";
import { EmptyState, LoadingState } from "@/components/Loading";
import { RestaurantGrid } from "@/components/RestaurantGrid";
import { ScrapeResults, SearchFiltersType } from "@/types";

import { useSurpriseRestaurant } from "@/hooks/useSurpriseRestaurant";
import { SurpriseModal } from "@/components/SurpriseModal";

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
  const [sortBy, setSortBy] = useState<"rating" | "delivery_time">("rating");

  const {
    getSurpriseRestaurant,
    surpriseRestaurant,
    isLoading: surpriseLoading,
    setSurpriseRestaurant,
    previousSuggestions,
    resetSuggestions,
  } = useSurpriseRestaurant();

  const [showSurpriseModal, setShowSurpriseModal] = useState(false);

  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [cacheInfo, setCacheInfo] = useState<{
    hasCache: boolean;
    age?: number;
    location?: string;
  }>({ hasCache: false });

  const [suggestions, setSuggestions] = useState<
    google.maps.places.AutocompletePrediction[]
  >([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Map refs
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  // Initialize map
  const initializeMap = useCallback(() => {
    if (!mapContainerRef.current) return;

    const defaultCenter = { lat: 23.8103, lng: 90.4125 };

    const mapOptions: google.maps.MapOptions = {
      center: defaultCenter,
      zoom: 14,
      styles: [
        {
          featureType: "poi",
          elementType: "labels",
          stylers: [{ visibility: "off" }],
        },
      ],
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    };

    const map = new window.google.maps.Map(mapContainerRef.current, mapOptions);
    mapRef.current = map;

    const marker = new window.google.maps.Marker({
      position: defaultCenter,
      map: map,
      draggable: true,
      animation: window.google.maps.Animation.DROP,
    });
    markerRef.current = marker;

    marker.addListener("dragend", () => {
      const position = marker.getPosition();
      if (position) {
        setSelectedLocation({
          lat: position.lat(),
          lng: position.lng(),
        });
      }
    });

    map.addListener("click", (e: google.maps.MapMouseEvent) => {
      const clickedLocation = {
        lat: e.latLng!.lat(),
        lng: e.latLng!.lng(),
      };

      setSelectedLocation(clickedLocation);
      marker.setPosition(clickedLocation);
    });

    const inputElement = document.getElementById(
      "location-search"
    ) as HTMLInputElement;
    if (inputElement) {
      const autocompleteOptions: google.maps.places.AutocompleteOptions = {
        fields: ["address_components", "geometry", "name"],
        types: ["address"],
      };

      const autocomplete = new window.google.maps.places.Autocomplete(
        inputElement,
        autocompleteOptions
      );

      autocomplete.bindTo("bounds", map);
      autocompleteRef.current = autocomplete;

      autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();

        if (!place.geometry || !place.geometry.location) {
          setError("No location details available for this address");
          return;
        }

        const location = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
        };

        setSelectedLocation(location);
        map.setCenter(location);
        marker.setPosition(location);
        map.setZoom(17);

        setSuggestions([]);
        setShowSuggestions(false);
      });
    }
  }, []);

  // Load Google Maps script
  useEffect(() => {
    const loadGoogleMapsScript = () => {
      const googleMapScript = document.createElement("script");
      googleMapScript.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`;
      googleMapScript.async = true;
      googleMapScript.defer = true;
      window.document.body.appendChild(googleMapScript);

      window.initMap = initializeMap;

      return () => {
        window.document.body.removeChild(googleMapScript);
        delete window.initMap;
      };
    };

    if (!window.google) {
      loadGoogleMapsScript();
    } else {
      initializeMap();
    }
  }, [initializeMap]);

  useEffect(() => {
    const cached = RestaurantCache.load();
    if (cached) {
      setRestaurants(cached.restaurants as ScrapeResults);
      setSelectedLocation(cached.location);
      setSearchValue(cached.searchText);
      setCacheInfo(RestaurantCache.getCacheInfo());
    }
  }, []);

  const fetchRestaurants = async (forceRefresh = false) => {
    const currentLocation = selectedLocation || { lat: 23.8103, lng: 90.4125 };
    const currentSearchText = searchValue || "Matikata";

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
          lat: 23.8103,
          lng: 90.4125,
          text: "Matikata",
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
      <header className="bg-white/80 backdrop-blur-lg border-b border-surface-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-brand-primary to-brand-secondary rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">K</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-brand-primary to-brand-secondary bg-clip-text text-transparent">
                  Khabo ki?
                </h1>
                <p className="text-surface-600  text-sm">
                  Find your perfect meal
                </p>
              </div>
            </div>

            {/* Cache Info */}
            {cacheInfo.hasCache && (
              <div className="flex items-center gap-3">
                <Badge
                  variant="outline"
                  className="bg-brand-success/10 text-brand-success border-brand-success/20"
                >
                  <div className="w-2 h-2 bg-brand-success rounded-full mr-2"></div>
                  Cached {cacheInfo.age}m ago
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearCache}
                  className="text-surface-600 hover:text-surface-900"
                >
                  Clear Cache
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Location Selection Card */}
        <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-surface-900">
                  Select your location
                </h2>
                <p className="text-surface-600 text-sm mt-1">
                  Choose where you want to order from
                </p>
              </div>
              {hasResults && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchRestaurants(true)}
                  className="flex items-center gap-2 border-brand-primary/20 text-brand-primary hover:bg-brand-primary/5"
                >
                  <RefreshCw size={16} />
                  Refresh
                </Button>
              )}
            </div>

            {/* Search input */}
            <div className="mb-6 flex gap-3">
              <div className="relative flex-1">
                <Input
                  id="location-search"
                  placeholder="Enter your address..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="pl-10 h-12 border-surface-300 focus:border-brand-primary focus:ring-brand-primary/20"
                />
                <MapPin
                  size={18}
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-surface-400"
                />
              </div>
              <Button
                onClick={() => fetchRestaurants()}
                disabled={isLoading}
                className="h-12 px-6 "
              >
                {isLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Search size={18} />
                )}
              </Button>
            </div>

            {/* Map container */}
            <div
              ref={mapContainerRef}
              className="w-full h-[300px] rounded-xl border border-surface-200 overflow-hidden"
            ></div>

            {/* Location info */}
            {selectedLocation && (
              <div className="mt-4 flex justify-between items-center p-4 bg-surface-100 rounded-lg">
                <p className="text-sm text-surface-600">
                  📍 Selected: {selectedLocation.lat.toFixed(5)},{" "}
                  {selectedLocation.lng.toFixed(5)}
                </p>
                <Button
                  onClick={() => fetchRestaurants()}
                  disabled={isLoading}
                  className=""
                >
                  {isLoading ? (
                    <span className="flex items-center">
                      <Loader2 size={18} className="mr-2 animate-spin" />
                      Finding restaurants...
                    </span>
                  ) : (
                    "Find Restaurants"
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

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
                      </div>
                    </div>
                  </div>

                  {/* Right side - Surprise Me Button */}
                  <Button
                    onClick={handleSurpriseMe}
                    disabled={surpriseLoading}
                    className="bg-gradient-to-r from-brand-accent to-brand-secondary hover:from-brand-accent/90 hover:to-brand-secondary/90 shadow-lg"
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

        {!isLoading && !hasResults && restaurants && <EmptyState />}
      </main>

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