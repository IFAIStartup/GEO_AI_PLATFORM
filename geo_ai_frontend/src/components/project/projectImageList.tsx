import React, { useState, MouseEvent } from "react";
import {
  Box,
  Button,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Checkbox,
  Modal,
} from "@mui/material";
import { LazyLoadImage } from "react-lazy-load-image-component";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import CloseIcon from "@mui/icons-material/Close";

import { useProjectStore } from "@store/project.store";
import { ProjectStatus } from "@models/project";

export const ProjectImageList: React.FC = () => {
  const projectStatus = useProjectStore((state) => state.project.status);
  const toggleImage = useProjectStore((state) => state.toggleImage);
  const { images } = useProjectStore((state) => ({
    images: state.project.images || [],
  }));

  const [modalImage, setModalImage] = useState<string | undefined>();

  const handleModalOpen = (imagePath: string) => {
    setModalImage(imagePath);
  };

  const handleModalClose = () => {
    setModalImage(undefined);
  };

  const onImageSelect = (
    e: MouseEvent<HTMLButtonElement>,
    imagePath: string
  ) => {
    e.stopPropagation();

    toggleImage(imagePath);
  };

  return (
    <>
      <ImageList sx={{ margin: 0 }} cols={6} rowHeight={88} gap={8}>
        {images.map((image) => (
          <ImageListItem
            key={image.name}
            onClick={() => handleModalOpen(image.path)}
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
              src={import.meta.env.VITE_SERVER_URL + "/" + image.path}
            />
            {projectStatus === ProjectStatus.Initial && (
              <ImageListItemBar
                position="top"
                actionIcon={
                  <Checkbox
                    onClick={(e) => onImageSelect(e, image.path)}
                    checked={!!image.graphic}
                    disableRipple
                    sx={{
                      backgroundColor: "#fff",
                      p: 0,
                      m: 1.5,
                      borderRadius: "2px",
                    }}
                  />
                }
                sx={{ background: "none" }}
              ></ImageListItemBar>
            )}
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
      <Modal open={!!modalImage} onClose={handleModalClose}>
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
          <img
            src={import.meta.env.VITE_SERVER_URL + "/" + modalImage}
            style={{
              maxWidth: "90vw",
              maxHeight: "90vh",
            }}
          />
          <Button
            variant="contained"
            color="inherit"
            onClick={handleModalClose}
            sx={{
              position: "absolute",
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
