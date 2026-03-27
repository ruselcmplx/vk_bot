package vk

import (
	"context"
	"math/rand"

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
	SetActivity(peerID int, activity string) error
	GetUserFirstName(userID int) (string, error)
	Shutdown()
}

type SDKClient struct {
	vk *api.VK
	lp *longpoll.LongPoll
}

func New(token string, groupID int) (*SDKClient, error) {
	client := api.NewVK(token)
	lp, err := longpoll.NewLongPoll(client, groupID)
	if err != nil {
		return nil, err
	}
	return &SDKClient{vk: client, lp: lp}, nil
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
