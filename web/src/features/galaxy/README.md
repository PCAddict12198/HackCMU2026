# galaxy (P3)
Baseline: one sphere per dish at `DishPoint.xyz`, colored by cuisine, click to select, hover label,
dashed line + wireframe marker from the selected dish to `shiftResult.target_xyz`.

TODO
- [ ] instancedMesh for stars (smooth with `?mockLarge=1`)
- [ ] camera fly-to on select (lerp the OrbitControls target)
- [ ] smooth target glide (lerp between successive `target_xyz`)
- [ ] highlight halos for `highlightIds` / `twinHighlight`
- [ ] PCA axis labels from `space.pca.axis_labels`
- [ ] dim extended-tier stars (`tier === "extended"`); recipe star from RecipeResponse.xyz
- [ ] legend for cuisines
