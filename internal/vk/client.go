package vk

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"mime/multipart"
	"net/http"

	"github.com/SevereCloud/vksdk/v3/api"
	"github.com/SevereCloud/vksdk/v3/events"
	longpoll "github.com/SevereCloud/vksdk/v3/longpoll-bot"
)

type Message struct {
	Text   string
	PeerID int
	FromID int
	Date   int64
}

type Client interface {
	Listen(ctx context.Context, handler func(Message)) error
	SendMessage(peerID int, msg string) error
	SendPhoto(peerID int, image []byte, caption string) error
	SetActivity(peerID int, activity string) error
	GetUserFirstName(userID int) (string, error)
	Shutdown()
}

type SDKClient struct {
	vk      *api.VK
	lp      *longpoll.LongPoll
	groupID int
}

func New(token string, groupID int) (*SDKClient, error) {
	client := api.NewVK(token)
	lp, err := longpoll.NewLongPoll(client, groupID)
	if err != nil {
		return nil, err
	}
	return &SDKClient{vk: client, lp: lp, groupID: groupID}, nil
}

func (c *SDKClient) Listen(ctx context.Context, handler func(Message)) error {
	c.lp.MessageNew(func(_ context.Context, obj events.MessageNewObject) {
		handler(Message{
			Text:   obj.Message.Text,
			PeerID: obj.Message.PeerID,
			FromID: obj.Message.FromID,
			Date:   int64(obj.Message.Date),
		})
	})
	return c.lp.RunWithContext(ctx)
}

func (c *SDKClient) SendMessage(peerID int, msg string) error {
	_, err := c.vk.MessagesSend(api.Params{
		"peer_id":   peerID,
		"message":   msg,
		"random_id": rand.Int(),
	})
	return err
}

func (c *SDKClient) SendPhoto(peerID int, image []byte, caption string) error {
	server, err := c.vk.PhotosGetMessagesUploadServer(api.Params{
		"peer_id": peerID,
	})
	if err != nil {
		return err
	}

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	part, err := writer.CreateFormFile("photo", "image.png")
	if err != nil {
		return err
	}
	if _, err := part.Write(image); err != nil {
		return err
	}
	if err := writer.Close(); err != nil {
		return err
	}

	req, err := http.NewRequest(http.MethodPost, server.UploadURL, &body)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("upload failed status=%d body=%s", resp.StatusCode, string(respBody))
	}

	var uploadResult struct {
		Server int    `json:"server"`
		Photo  string `json:"photo"`
		Hash   string `json:"hash"`
	}
	if err := json.Unmarshal(respBody, &uploadResult); err != nil {
		return err
	}
	if uploadResult.Server == 0 || uploadResult.Photo == "" || uploadResult.Hash == "" {
		return fmt.Errorf("invalid upload response: %s", string(respBody))
	}

	saved, err := c.vk.PhotosSaveMessagesPhoto(api.Params{
		"server": uploadResult.Server,
		"photo":  uploadResult.Photo,
		"hash":   uploadResult.Hash,
	})
	if err != nil {
		return err
	}
	if len(saved) == 0 {
		return fmt.Errorf("empty save photo response")
	}

	_, err = c.vk.MessagesSend(api.Params{
		"peer_id":    peerID,
		"message":    caption,
		"attachment": saved[0].ToAttachment(),
		"random_id":  rand.Int(),
	})
	return err
}

func (c *SDKClient) SetActivity(peerID int, activity string) error {
	_, err := c.vk.MessagesSetActivity(api.Params{
		"peer_id": peerID,
		"type":    activity,
	})
	return err
}

func (c *SDKClient) GetUserFirstName(userID int) (string, error) {
	resp, err := c.vk.UsersGet(api.Params{"user_ids": userID})
	if err != nil || len(resp) == 0 {
		return "", err
	}
	return resp[0].FirstName, nil
}

func (c *SDKClient) Shutdown() {
	c.lp.Shutdown()
}
