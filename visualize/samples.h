#pragma once

#include <string>

// Small samples for scatter / simple polygons (readable in the gallery).
constexpr int GALLERY_N = 80;
constexpr int GALLERY_COORD = 1000;

// Convex polygon gallery: small preview and large (dense markers).
constexpr int GALLERY_CONVEX_N = 80;
constexpr long long GALLERY_CONVEX_COORD = 1000;
constexpr int GALLERY_CONVEX_LARGE_N = 15000;
constexpr long long GALLERY_CONVEX_LARGE_COORD = 3'000'000'000LL;

// General-position scatter (both libraries; jngen is O(n²) rejection).
constexpr int GALLERY_GENERAL_POSITION_N = 2000;
constexpr long long GALLERY_GENERAL_POSITION_COORD = 3'000'000LL;

// Gallery variants: seeds GALLERY_SEED_BASE .. GALLERY_SEED_BASE + COUNT - 1.
constexpr int GALLERY_SEED_BASE = 42;
constexpr int GALLERY_VARIANT_COUNT = 20;

inline std::string gallery_seed_tag(int seed) {
	return "_s" + std::to_string(seed);
}
