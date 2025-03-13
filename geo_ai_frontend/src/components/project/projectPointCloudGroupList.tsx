import React, { useState, MouseEvent, Suspense } from "react";
import {
  Box,
  Button,
  ImageList,
  ImageListItem,
  Checkbox,
  Modal,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
} from "@mui/material";
import { LazyLoadImage } from "react-lazy-load-image-component";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MapsHomeWorkIcon from "@mui/icons-material/MapsHomeWork";
import { grey } from "@mui/material/colors";

import { useProjectStore } from "@store/project.store";
import { ProjectFileGroup, ProjectStatus } from "@models/project";
import { PointCloudScene } from "@components/point-cloud/scene";

export const ProjectPointCloudGroupList: React.FC = () => {
  const projectStatus = useProjectStore((state) => state.project.status);
  const togglePointCloudGroup = useProjectStore(
    (state) => state.togglePointCloudGroup
  );
  const { pointCloudGroups } = useProjectStore((state) => ({
    pointCloudGroups: state.project.pointCloudGroups || [],
  }));

  const [modalPointCloud, setModalPointCloud] = useState<string | undefined>();
  const [modalImage, setModalImage] = useState<string | undefined>();

  const handleImageModalOpen = (imgPath: string) => {
    setModalImage(imgPath);
  };

  const handlePointCloudModalOpen = (pcdPath?: string) => {
    if (!pcdPath) {
      return;
    }

    setModalPointCloud(pcdPath);
  };

  const handleModalClose = () => {
    setModalImage(undefined);
    setModalPointCloud(undefined);
  };

  const onPointCloudSelect = (
    e: MouseEvent<HTMLButtonElement>,
    group: ProjectFileGroup
  ) => {
    e.stopPropagation();

    togglePointCloudGroup(group.title);
  };

  return (
    <>
      {pointCloudGroups.map((group, index) => (
        <Accordion key={index}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              ".MuiAccordionSummary-content": {
                alignItems: "center",
              },
            }}
          >
            {projectStatus === ProjectStatus.Initial && (
              <Checkbox
                disableRipple
                checked={group.selected || false}
                onClick={(e) => onPointCloudSelect(e, group)}
                inputProps={{ "aria-label": "controlled" }}
              />
            )}
            {group.title}
          </AccordionSummary>
          <AccordionDetails>
            <ImageList sx={{ margin: 0 }} cols={6} rowHeight={88} gap={8}>
              {group.pcdPath && (
                <ImageListItem
                  onClick={() => handlePointCloudModalOpen(group.pcdPath)}
                  sx={{
                    borderRadius: "4px",
                    overflow: "hidden",
                    cursor: "pointer",
                    border: "2px solid transparent",
                    justifyContent: "center",
                    alignItems: "center",
                    borderColor: grey[500],
                    "&:hover": {
                      borderColor: "primary.main",
                    },
                  }}
                >
                  <MapsHomeWorkIcon color="primary" sx={{ fontSize: 40 }} />
                </ImageListItem>
              )}
              {group.images.map((img) => (
                <ImageListItem
                  key={img.name}
                  onClick={() => handleImageModalOpen(img.path)}
                  sx={{
                    borderRadius: "4px",
                    overflow: "hidden",
                    cursor: "pointer",
                    border: "2px solid transparent",
                    "&:hover": {
                      borderColor: "primary.main",
                      ".zoom-icon": {
                        display: "block",
                      },
                    },
                  }}
                >
                  <LazyLoadImage
                    src={import.meta.env.VITE_SERVER_URL + "/" + img.path}
                  />
                  <ZoomInIcon
                    className="zoom-icon"
                    fontSize="large"
                    sx={{
                      position: "absolute",
                      top: 0,
                      right: 0,
                      bottom: 0,
                      left: 0,
                      m: "auto",
                      color: "#fff",
                      display: "none",
                    }}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          </AccordionDetails>
        </Accordion>
      ))}
      <Modal
        open={!!modalImage || !!modalPointCloud}
        onClose={handleModalClose}
      >
        <Box
          component="div"
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            bgcolor: "background.paper",
            boxShadow: 24,
            outline: "none",
          }}
        >
          {modalImage && (
            <img
              src={import.meta.env.VITE_SERVER_URL + "/" + modalImage}
              style={{
                maxWidth: "90vw",
                maxHeight: "90vh",
              }}
            />
          )}
          {modalPointCloud && (
            <Box
              component="div"
              sx={{
                width: "90vw",
                height: "80vh",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <Suspense fallback={<CircularProgress />}>
                <PointCloudScene path={modalPointCloud} />
              </Suspense>
            </Box>
          )}
          <Button
            variant="contained"
            color="inherit"
            onClick={handleModalClose}
            sx={{
              position: "absolute",
              top: 0,
              right: 0,
              m: 2,
              p: 1,
              minWidth: "auto",
              boxShadow: 2,
            }}
          >
            <CloseIcon />
          </Button>
        </Box>
      </Modal>
    </>
  );
};
