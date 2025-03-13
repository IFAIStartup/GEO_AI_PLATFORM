import TextContent from "@arcgis/core/popup/content/TextContent";

import i18n from "../i18n";

export const getPopupTemplateContent = (feature: __esri.Feature) => {
  let table = '<table cellspacing="0" width="100%">';
  const name = feature.graphic.getAttribute("name")?.trim();
  const oldName = feature.graphic.getAttribute("name_old")?.trim();
  const newName = feature.graphic.getAttribute("name_new")?.trim();
  const type = feature.graphic.getAttribute("type")?.trim();
  const text = feature.graphic.getAttribute("text")?.trim();

  if (name) {
    table += `<tr><td><b>${i18n.t("map.name")}</b></td><td>${name}</td></tr>`;
  }

  if (newName) {
    table += `<tr><td><b>${i18n.t(
      "map.newName"
    )}</b></td><td>${newName}</td></tr>`;
  }

  if (oldName) {
    table += `<tr><td><b>${i18n.t(
      "map.oldName"
    )}</b></td><td>${oldName}</td></tr>`;
  }

  if (type) {
    table += `<tr><td><b>${i18n.t("map.type")}</b></td><td>${type}</td></tr>`;
  }

  if (text) {
    table += `<tr><td><b>${i18n.t("map.text")}</b></td><td>${text}</td></tr>`;
  }

  let point: __esri.Point | undefined;
  if (feature.graphic.geometry.type === "point") {
    point = feature.graphic.geometry as __esri.Point;
  } else if (feature.graphic.geometry.type === "polygon") {
    point = (feature.graphic.geometry as __esri.Polygon).centroid;
  }
  table += `<tr><td><b>${i18n.t("map.lat")}</b></td><td>${
    point?.latitude
  }</td></tr>`;
  table += `<tr><td><b>${i18n.t("map.long")}</b></td><td>${
    point?.longitude
  }</td></tr>`;

  table += "</table>";

  const textEl = new TextContent();
  textEl.text = table;
  return [textEl];
};
