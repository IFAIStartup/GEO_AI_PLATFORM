import React, { useState, ChangeEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Typography,
  TextField,
  Collapse,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  Checkbox,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from "@mui/material";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";

import { useMLStore } from "@store/ml.store";
import { MLModel } from "@models/ml";

const EPOCH_COUNT_MAX = 1000;
const SCALE_FACTOR_MIN = 0.025;
const SCALE_FACTOR_MAX = 40;

export const TrainModelStep: React.FC<{ model: MLModel }> = ({ model }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const startTraining = useMLStore((state) => state.startTraining);
  const modelTypes = useMLStore((state) => state.modelTypes);

  const [type, setType] = useState("");
  const [epoch, setEpoch] = useState("1");
  const [epochError, setEpochError] = useState("");
  const [scaleFactor, setScaleFactor] = useState("1");
  const [scaleFactorError, setScaleFactorError] = useState("");
  const [expandedClassList, setExpandedClassList] = useState(false);
  const [expandedObjectList, setExpandedObjectList] = useState(true);
  const [checkedObjects, setCheckedObjects] = useState<string[]>([]);

  useEffect(() => {
    if (modelTypes.length) {
      setType(modelTypes[0]);
    }
  }, [modelTypes]);

  const handleTypeChange = (event: SelectChangeEvent) => {
    setType(event.target.value as string);
  };

  const onEpochChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setEpoch(e.target.value);
    const value = +e.target.value;
    if (value < 1) {
      setEpochError(t("ml.epochWarning1"));
    } else if (value > EPOCH_COUNT_MAX) {
      setEpochError(t("ml.epochWarning2", { max: EPOCH_COUNT_MAX }));
    } else if (!Number.isInteger(value)) {
      setEpochError(t("ml.epochWarning3"));
    } else {
      setEpochError("");
    }
  };

  const onScaleFactorChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setScaleFactor(e.target.value);
    const value = +e.target.value;
    if (value < SCALE_FACTOR_MIN) {
      setScaleFactorError(
        t("ml.scaleFactorWarning1", { min: SCALE_FACTOR_MIN })
      );
    } else if (value > SCALE_FACTOR_MAX) {
      setScaleFactorError(
        t("ml.scaleFactorWarning2", { max: SCALE_FACTOR_MAX })
      );
    } else if (!Number.isFinite(value)) {
      setScaleFactorError(t("ml.scaleFactorWarning3"));
    } else {
      setScaleFactorError("");
    }
  };

  const handleClassListExpand = () => {
    setExpandedClassList(!expandedClassList);
  };

  const handleObjectListExpand = () => {
    setExpandedObjectList(!expandedObjectList);
  };

  const handleObjectClick = (obj: string) => () => {
    const currentIndex = checkedObjects.indexOf(obj);
    const newChecked = [...checkedObjects];

    if (currentIndex === -1) {
      newChecked.push(obj);
    } else {
      newChecked.splice(currentIndex, 1);
    }

    setCheckedObjects(newChecked);
  };

  const onCancel = () => {
    navigate("/ml");
  };

  const onStartTraining = () => {
    startTraining({
      id: model.id,
      type_model: type,
      epochs: +epoch,
      scale_factor: +scaleFactor,
      classes: checkedObjects,
    });
  };

  return (
    <>
      <Box
        component="div"
        sx={{
          flexGrow: 1,
          minWidth: 500,
        }}
      >
        <Typography variant="h5">
          {model.name} {t("ml.trainStepTitle")}
        </Typography>
        <Box
          component="div"
          sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 4 }}
        >
          <TextField
            fullWidth
            id="name"
            label={t("ml.createStepTypeField")}
            value={model.type_of_data
              .map((type) => t(`types.${type}`))
              .join(", ")}
            disabled
          />
          <FormControl fullWidth>
            <InputLabel id="type-select-label">{t("ml.modelType")}</InputLabel>
            <Select
              labelId="type-select-label"
              id="type-select"
              value={type}
              label={t("ml.modelType")}
              onChange={handleTypeChange}
            >
              {modelTypes.map((t, i) => (
                <MenuItem value={t} key={i}>
                  {t}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            required
            fullWidth
            id="epoch"
            label={t("ml.trainEpochField")}
            value={epoch}
            type="text"
            onChange={onEpochChange}
            error={!!epochError}
            helperText={epochError}
          />
          <TextField
            required
            fullWidth
            id="scalefactor"
            label={t("ml.scaleFactorField")}
            value={scaleFactor}
            type="text"
            onChange={onScaleFactorChange}
            error={!!scaleFactorError}
            helperText={scaleFactorError}
          />
          <Box component="div">
            <Button
              variant="text"
              fullWidth
              startIcon={expandedClassList ? <ExpandLess /> : <ExpandMore />}
              disabled={!model.task_result?.classes.length}
              onClick={handleClassListExpand}
              sx={{
                "&.Mui-disabled": {
                  color: "rgba(0, 0, 0, 0.26)",
                  backgroundColor: "transparent",
                },
              }}
            >
              {t("ml.listOfClasses")}
            </Button>
            <Collapse in={expandedClassList} timeout="auto">
              <List>
                {model.task_result?.classes.map((clss, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemText primary={clss} />
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </Box>
          <Box component="div">
            <Button
              variant="text"
              fullWidth
              startIcon={expandedObjectList ? <ExpandLess /> : <ExpandMore />}
              disabled={!model.task_result?.objects.length}
              onClick={handleObjectListExpand}
              sx={{
                "&.Mui-disabled": {
                  color: "rgba(0, 0, 0, 0.26)",
                  backgroundColor: "transparent",
                },
              }}
            >
              {t("ml.listOfObjects")}
            </Button>
            <Collapse in={expandedObjectList} timeout="auto">
              <List>
                {model.task_result?.objects.map((obj, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemButton
                      role={undefined}
                      onClick={handleObjectClick(obj)}
                      dense
                    >
                      <ListItemIcon>
                        <Checkbox
                          edge="start"
                          checked={checkedObjects.indexOf(obj) !== -1}
                          tabIndex={-1}
                          disableRipple
                        />
                      </ListItemIcon>
                      <ListItemText primary={obj} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </Box>
        </Box>
      </Box>
      <Box component="div" sx={{ display: "flex", gap: 1.5, minWidth: 500 }}>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
        <Button
          variant="contained"
          fullWidth
          onClick={onStartTraining}
          disabled={!type || !!epochError || !checkedObjects.length}
        >
          {t("ml.trainButton")}
        </Button>
      </Box>
    </>
  );
};
