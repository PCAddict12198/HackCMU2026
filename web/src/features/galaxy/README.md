# galaxy (P3)
Baseline: one sphere per dish at `DishPoint.xyz`, colored by cuisine, click to select, hover label,
dashed line + wireframe marker from the selected dish to `shiftResult.target_xyz`.

TODO
- [x] instancedMesh for stars (smooth with `?mockLarge=1`)
- [x] camera fly-to on select (lerp the OrbitControls target)
- [x] smooth target glide (lerp between successive `target_xyz`)
- [x] highlight halos for `highlightIds` / `twinHighlight`
- [x] PCA axis labels from `space.pca.axis_labels`
- [x] dim extended-tier stars (`tier === "extended"`); recipe star from RecipeResponse.xyz
- [x] legend for cuisines
